from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_ingestion.github_api import (
    collect_repos,
    fetch_comments_for_issue,
    fetch_issues,
    request_json,
    split_repo,
)
from src.mcp_tools.database_tool import insert_records
from src.utils.config import GITHUB_API_BASE, GITHUB_TOKEN


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def github_fetch_issues(input_data: dict[str, Any]) -> dict[str, Any]:
    repo_name = input_data["repo"]
    max_issues = int(input_data.get("max_issues", 20))
    state = input_data.get("state", "all")
    issues = fetch_issues(repo_name, max_issues=max_issues, state=state)
    return {
        "success": True,
        "tool": "github.fetch_issues",
        "github_token_detected": bool(GITHUB_TOKEN),
        "data": issues,
        "meta": {
            "repo": repo_name,
            "issues_seen": len(issues),
        },
    }


def github_fetch_comments(input_data: dict[str, Any]) -> dict[str, Any]:
    repo_name = input_data["repo"]
    issue_id = str(input_data["issue_id"])
    max_comments = int(input_data.get("max_comments", 50))
    comments = fetch_comments_for_issue(repo_name, issue_id, max_comments=max_comments)
    return {
        "success": True,
        "tool": "github.fetch_comments",
        "github_token_detected": bool(GITHUB_TOKEN),
        "data": comments,
        "meta": {
            "repo": repo_name,
            "issue_id": issue_id,
            "comments_seen": len(comments),
        },
    }


def github_fetch_repo_feedback(input_data: dict[str, Any]) -> dict[str, Any]:
    repos = input_data.get("repos") or [input_data["repo"]]
    max_issues = int(input_data.get("max_issues", 20))
    include_comments = bool(input_data.get("include_comments", False))
    save_to_db = bool(input_data.get("save_to_db", True))

    records, summaries = collect_repos(repos, max_issues=max_issues, include_comments=include_comments)
    insert_result = insert_records("raw_feedback", records) if save_to_db else None

    return {
        "success": True,
        "tool": "github.fetch_repo_feedback",
        "github_token_detected": bool(GITHUB_TOKEN),
        "save_to_db": save_to_db,
        "insert_result": insert_result,
        "data": records,
        "meta": {
            "records_seen": len(records),
            "summaries": summaries,
        },
    }


def github_fetch_releases(input_data: dict[str, Any]) -> dict[str, Any]:
    repo_name = input_data["repo"]
    max_items = int(input_data.get("max_items", 20))
    owner, repo = split_repo(repo_name)
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/releases?per_page={min(100, max_items)}"
    releases = request_json(url)[:max_items]
    data = [
        {
            "release_id": release.get("id"),
            "repo_name": repo_name,
            "tag_name": release.get("tag_name"),
            "title": release.get("name"),
            "body": release.get("body") or "",
            "published_at": release.get("published_at"),
            "url": release.get("html_url"),
        }
        for release in releases
    ]
    return {
        "success": True,
        "tool": "github.fetch_releases",
        "github_token_detected": bool(GITHUB_TOKEN),
        "data": data,
        "meta": {
            "repo": repo_name,
            "releases_seen": len(data),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="MCP-style GitHub tool wrapper.")
    parser.add_argument("--repo", help="GitHub repo, e.g. streamlit/streamlit.")
    parser.add_argument("--max-issues", type=int, default=5)
    parser.add_argument("--include-comments", action="store_true")
    parser.add_argument("--releases", action="store_true")
    parser.add_argument("--no-save", action="store_true")
    args = parser.parse_args()

    if not args.repo:
        parser.print_help()
        return

    if args.releases:
        result = github_fetch_releases({"repo": args.repo})
    else:
        result = github_fetch_repo_feedback(
            {
                "repo": args.repo,
                "max_issues": args.max_issues,
                "include_comments": args.include_comments,
                "save_to_db": not args.no_save,
            }
        )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
