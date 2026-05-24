from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import insert_records
from src.utils.config import GITHUB_API_BASE, GITHUB_TOKEN


TEMPORARY_HTTP_CODES = {502, 503, 504}


class GitHubRateLimitError(RuntimeError):
    """Raised when GitHub API rate limit is reached."""


class GitHubRequestError(RuntimeError):
    """Raised when GitHub API returns a non-retryable request error."""


def stable_id(*parts: Any) -> str:
    raw = "::".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def format_rate_limit_reset(headers: Any) -> str:
    reset_value = headers.get("X-RateLimit-Reset")
    if reset_value:
        try:
            reset_time = datetime.fromtimestamp(int(reset_value), tz=timezone.utc)
            return reset_time.isoformat()
        except (TypeError, ValueError):
            return str(reset_value)

    retry_after = headers.get("Retry-After")
    if retry_after:
        return f"retry after {retry_after} seconds"

    date_value = headers.get("Date")
    if date_value:
        try:
            return parsedate_to_datetime(date_value).isoformat()
        except (TypeError, ValueError):
            return str(date_value)

    return "unknown"


def build_rate_limit_message(error: urllib.error.HTTPError, detail: str) -> str:
    token_status = "detected" if GITHUB_TOKEN else "missing"
    reset_time = format_rate_limit_reset(error.headers)
    return (
        "GitHub API rate limit reached. "
        f"status={error.code}; github_token={token_status}; reset={reset_time}. "
        "Set GITHUB_TOKEN for a higher limit, reduce --max-issues, or retry later. "
        f"GitHub response: {detail}"
    )


def request_json_once(url: str) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "ai-product-research-copilot",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        if error.code in {403, 429} and "rate limit" in detail.lower():
            raise GitHubRateLimitError(build_rate_limit_message(error, detail)) from error
        if error.code in TEMPORARY_HTTP_CODES:
            raise
        raise GitHubRequestError(f"GitHub API error {error.code}: {detail}") from error


def request_json(url: str, max_retries: int = 3) -> Any:
    for attempt in range(max_retries + 1):
        try:
            return request_json_once(url)
        except GitHubRateLimitError:
            raise
        except GitHubRequestError:
            raise
        except urllib.error.HTTPError as error:
            if error.code not in TEMPORARY_HTTP_CODES or attempt >= max_retries:
                raise GitHubRequestError(f"GitHub API temporary error {error.code}: {error.reason}") from error
        except (urllib.error.URLError, TimeoutError) as error:
            if attempt >= max_retries:
                raise GitHubRequestError(f"GitHub network error after retries: {error}") from error

        wait_seconds = 2**attempt
        print(f"Temporary GitHub request failure. Retry {attempt + 1}/{max_retries} after {wait_seconds}s...")
        time.sleep(wait_seconds)

    raise GitHubRequestError("GitHub request failed after retries.")


def split_repo(repo_full_name: str) -> tuple[str, str]:
    if "/" not in repo_full_name:
        raise ValueError(f"Repo must be owner/repo, got: {repo_full_name}")
    owner, repo = repo_full_name.split("/", 1)
    return owner, repo


def normalize_issue(repo_full_name: str, issue: dict[str, Any]) -> dict[str, Any]:
    issue_id = str(issue.get("number"))
    labels = [label.get("name") for label in issue.get("labels", []) if isinstance(label, dict)]
    return {
        "feedback_id": stable_id("github", repo_full_name, "issue", issue_id),
        "source": "github",
        "repo_name": repo_full_name,
        "issue_id": issue_id,
        "comment_id": None,
        "title": issue.get("title") or "",
        "body": issue.get("body") or "",
        "labels": json.dumps(labels, ensure_ascii=False),
        "state": issue.get("state") or "",
        "author": (issue.get("user") or {}).get("login"),
        "created_at": issue.get("created_at"),
        "updated_at": issue.get("updated_at"),
        "comments_count": int(issue.get("comments") or 0),
        "url": issue.get("html_url"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def normalize_comment(repo_full_name: str, issue_id: str, comment: dict[str, Any]) -> dict[str, Any]:
    comment_id = str(comment.get("id"))
    return {
        "feedback_id": stable_id("github", repo_full_name, "issue", issue_id, "comment", comment_id),
        "source": "github",
        "repo_name": repo_full_name,
        "issue_id": issue_id,
        "comment_id": comment_id,
        "title": "",
        "body": comment.get("body") or "",
        "labels": "[]",
        "state": "",
        "author": (comment.get("user") or {}).get("login"),
        "created_at": comment.get("created_at"),
        "updated_at": comment.get("updated_at"),
        "comments_count": 0,
        "url": comment.get("html_url"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def fetch_issues(repo_full_name: str, max_issues: int, state: str = "all") -> list[dict[str, Any]]:
    owner, repo = split_repo(repo_full_name)
    issues: list[dict[str, Any]] = []
    page = 1
    per_page = min(100, max_issues)

    while len(issues) < max_issues:
        query = urllib.parse.urlencode(
            {
                "state": state,
                "per_page": per_page,
                "page": page,
                "sort": "created",
                "direction": "desc",
            }
        )
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues?{query}"
        batch = request_json(url)
        if not batch:
            break

        for item in batch:
            if "pull_request" in item:
                continue
            issues.append(normalize_issue(repo_full_name, item))
            if len(issues) >= max_issues:
                break

        page += 1
        time.sleep(0.2)

    return issues


def fetch_comments_for_issue(repo_full_name: str, issue_id: str, max_comments: int = 50) -> list[dict[str, Any]]:
    owner, repo = split_repo(repo_full_name)
    query = urllib.parse.urlencode({"per_page": min(100, max_comments), "page": 1})
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_id}/comments?{query}"
    comments = request_json(url)[:max_comments]
    return [normalize_comment(repo_full_name, issue_id, comment) for comment in comments]


def load_sample(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    records: list[dict[str, Any]] = []
    for item in data:
        if item.get("comment_id"):
            records.append(item)
        else:
            records.append(item)
    return records


def summarize_records(repo_full_name: str, records: list[dict[str, Any]]) -> dict[str, Any]:
    issues_seen = sum(1 for record in records if not record.get("comment_id"))
    comments_seen = sum(1 for record in records if record.get("comment_id"))
    return {
        "repo": repo_full_name,
        "issues_seen": issues_seen,
        "comments_seen": comments_seen,
        "records_seen": len(records),
    }


def collect_repos(repos: list[str], max_issues: int, include_comments: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    per_repo = max(1, max_issues)

    for repo_full_name in repos:
        repo_records: list[dict[str, Any]] = []
        issues = fetch_issues(repo_full_name, per_repo)
        repo_records.extend(issues)
        if include_comments:
            for issue in issues:
                if issue["comments_count"] > 0:
                    repo_records.extend(fetch_comments_for_issue(repo_full_name, issue["issue_id"]))
                    time.sleep(0.2)
        records.extend(repo_records)
        summaries.append(summarize_records(repo_full_name, repo_records))

    return records, summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect GitHub Issues and Comments into raw_feedback.")
    parser.add_argument("--repos", nargs="*", default=[], help="GitHub repos, e.g. streamlit/streamlit.")
    parser.add_argument("--max-issues", type=int, default=100, help="Max issues per repo.")
    parser.add_argument("--include-comments", action="store_true", help="Also fetch issue comments.")
    parser.add_argument("--sample", default="", help="Load sample raw feedback JSON instead of calling GitHub.")
    args = parser.parse_args()

    if args.sample:
        records = load_sample(Path(args.sample))
        summaries = [summarize_records("sample", records)]
    else:
        if not args.repos:
            raise SystemExit("Please pass --repos owner/repo or --sample data/sample_raw_feedback.json")
        records, summaries = collect_repos(args.repos, args.max_issues, args.include_comments)

    result = insert_records("raw_feedback", records)
    print(
        json.dumps(
            {
                "raw_feedback": result,
                "records_seen": len(records),
                "github_token_detected": bool(GITHUB_TOKEN),
                "include_comments": args.include_comments,
                "summaries": summaries,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
