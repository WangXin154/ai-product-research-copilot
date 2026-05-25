from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import (  # noqa: E402
    get_cleaned_feedback,
    get_comment_summary,
    get_competitor_matrix,
    get_competitor_summary,
    get_feedback_samples,
    get_raw_feedback,
    get_repo_summary,
    get_topic_samples,
    get_topic_summary,
    query,
    table_counts,
)
from src.mcp_tools.evaluation_tool import score_output  # noqa: E402
from src.mcp_tools.export_tool import (  # noqa: E402
    export_cleaned_feedback_csv,
    export_repo_summary_json,
    export_research_summary_markdown,
)
from src.mcp_tools.github_tool import (  # noqa: E402
    github_fetch_comments,
    github_fetch_issues,
    github_fetch_releases,
    github_fetch_repo_feedback,
)


mcp = FastMCP("ai-product-research-copilot")


def compact_result(result: dict[str, Any], max_items: int | None = None) -> dict[str, Any]:
    if max_items is None:
        return result
    data = result.get("data")
    if isinstance(data, list):
        return {**result, "data": data[:max_items], "truncated": len(data) > max_items}
    return result


@mcp.tool()
def database_stats() -> dict[str, int]:
    """Return row counts for core product research tables."""
    return table_counts()


@mcp.tool()
def database_repo_summary() -> dict[str, Any]:
    """Return GitHub feedback counts grouped by repository."""
    return get_repo_summary()


@mcp.tool()
def database_comment_summary() -> dict[str, Any]:
    """Return GitHub comment counts grouped by repository."""
    return get_comment_summary()


@mcp.tool()
def database_query_raw_feedback(repo_name: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Query raw GitHub feedback records."""
    return get_raw_feedback(repo_name=repo_name, limit=limit)


@mcp.tool()
def database_query_cleaned_feedback(repo_name: str | None = None, limit: int = 20) -> dict[str, Any]:
    """Query cleaned product feedback records joined with source metadata."""
    return get_cleaned_feedback(repo_name=repo_name, limit=limit)


@mcp.tool()
def database_feedback_samples(limit: int = 5, include_comments: bool = True) -> dict[str, Any]:
    """Return sample raw feedback rows with URL evidence."""
    return get_feedback_samples(limit=limit, include_comments=include_comments)


@mcp.tool()
def database_topic_summary() -> dict[str, Any]:
    """Return AI-discovered topic counts, confidence, and sentiment summary."""
    return get_topic_summary()


@mcp.tool()
def database_topic_samples(limit: int = 10) -> dict[str, Any]:
    """Return topic examples with evidence previews and source URLs."""
    return get_topic_samples(limit=limit)


@mcp.tool()
def database_competitor_summary() -> dict[str, Any]:
    """Return competitor feature coverage summary."""
    return get_competitor_summary()


@mcp.tool()
def database_competitor_matrix() -> dict[str, Any]:
    """Return competitor feature matrix rows."""
    return get_competitor_matrix()


@mcp.tool()
def database_opportunity_summary(limit: int = 20) -> dict[str, Any]:
    """Return product opportunity scores ordered by priority score."""
    return query(
        """
        SELECT
            opportunity_id,
            opportunity_name,
            priority,
            priority_score,
            user_value,
            business_value,
            frequency,
            severity,
            effort,
            risk,
            ai_feasibility,
            evidence_strength,
            created_at
        FROM opportunity_scores
        ORDER BY priority_score DESC
        LIMIT ?
        """,
        (limit,),
    )


@mcp.tool()
def database_latest_prd() -> dict[str, Any]:
    """Return the latest PRD draft metadata and structured fields."""
    return query(
        """
        SELECT
            prd_id,
            opportunity_id,
            title,
            background,
            user_story,
            requirements,
            acceptance_criteria,
            metrics,
            risks,
            evidence_refs,
            status,
            created_at,
            updated_at
        FROM prd_drafts
        ORDER BY updated_at DESC, created_at DESC
        LIMIT 1
        """
    )


@mcp.tool()
def database_latest_evaluation() -> dict[str, Any]:
    """Return the latest AI evaluation result."""
    return query(
        """
        SELECT
            evaluation_id,
            output_id,
            output_type,
            relevance,
            accuracy,
            actionability,
            evidence_coverage,
            hallucination_risk,
            human_edit_rate,
            prd_completeness,
            overall_score,
            evaluation_notes,
            created_at
        FROM ai_evaluation_results
        ORDER BY created_at DESC
        LIMIT 1
        """
    )


@mcp.tool()
def github_fetch_repo_issues(repo: str, max_issues: int = 20, state: str = "all") -> dict[str, Any]:
    """Fetch GitHub Issues for a repository without saving to the database."""
    return github_fetch_issues({"repo": repo, "max_issues": max_issues, "state": state})


@mcp.tool()
def github_fetch_issue_comments(repo: str, issue_id: str, max_comments: int = 50) -> dict[str, Any]:
    """Fetch comments for one GitHub Issue."""
    return github_fetch_comments({"repo": repo, "issue_id": issue_id, "max_comments": max_comments})


@mcp.tool()
def github_fetch_repo_feedback_tool(
    repo: str,
    max_issues: int = 20,
    include_comments: bool = False,
    save_to_db: bool = True,
) -> dict[str, Any]:
    """Fetch GitHub Issues and optional Comments, optionally saving raw feedback to the database."""
    return github_fetch_repo_feedback(
        {
            "repo": repo,
            "max_issues": max_issues,
            "include_comments": include_comments,
            "save_to_db": save_to_db,
        }
    )


@mcp.tool()
def github_fetch_release_notes(repo: str, max_items: int = 20) -> dict[str, Any]:
    """Fetch GitHub release notes for a repository."""
    return github_fetch_releases({"repo": repo, "max_items": max_items})


@mcp.tool()
def evaluation_score_output(
    output_text: str,
    evidence_texts_json: str = "[]",
    output_type: str = "prd",
    save_to_db: bool = False,
    human_edit_rate: float | None = None,
) -> dict[str, Any]:
    """Evaluate AI output quality with evidence coverage and hallucination risk."""
    try:
        evidence_texts = json.loads(evidence_texts_json)
    except json.JSONDecodeError:
        evidence_texts = [evidence_texts_json]
    if isinstance(evidence_texts, str):
        evidence_texts = [evidence_texts]
    return score_output(
        {
            "output_text": output_text,
            "evidence_texts": evidence_texts,
            "output_type": output_type,
            "save_to_db": save_to_db,
            "human_edit_rate": human_edit_rate,
        }
    )


@mcp.tool()
def export_cleaned_feedback(limit: int = 1000, repo_name: str | None = None, output_dir: str | None = None) -> dict[str, Any]:
    """Export cleaned feedback to CSV."""
    payload: dict[str, Any] = {"limit": limit, "repo_name": repo_name}
    if output_dir:
        payload["output_dir"] = output_dir
    return export_cleaned_feedback_csv(payload)


@mcp.tool()
def export_repo_summary(output_dir: str | None = None) -> dict[str, Any]:
    """Export repository and comment summary to JSON."""
    payload: dict[str, Any] = {}
    if output_dir:
        payload["output_dir"] = output_dir
    return export_repo_summary_json(payload)


@mcp.tool()
def export_research_summary(output_dir: str | None = None) -> dict[str, Any]:
    """Export a Markdown research summary."""
    payload: dict[str, Any] = {}
    if output_dir:
        payload["output_dir"] = output_dir
    return export_research_summary_markdown(payload)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
