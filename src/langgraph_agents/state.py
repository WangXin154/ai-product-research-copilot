from __future__ import annotations

from typing import Any, TypedDict


class ResearchState(TypedDict, total=False):
    project_id: str
    project_name: str
    selected_repos: list[str]
    limit: int

    cleaned_feedback: list[dict[str, Any]]
    feedback_summary: dict[str, Any]

    topics: list[dict[str, Any]]
    pain_points: list[dict[str, Any]]

    opportunities: list[dict[str, Any]]
    selected_opportunity: dict[str, Any]

    prd_draft: dict[str, Any]
    evaluation_report: dict[str, Any]

    bi_metrics: dict[str, Any]
    product_review_summary: str

    errors: list[dict[str, Any]]
    current_step: str


def add_error(state: ResearchState, step: str, message: str) -> ResearchState:
    errors = state.setdefault("errors", [])
    errors.append({"step": step, "message": message})
    return state

