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

    competitor_features: list[dict[str, Any]]
    competitor_matrix: list[dict[str, Any]]
    competitor_insights: list[dict[str, Any]]
    differentiation_opportunities: list[dict[str, Any]]
    competitor_review_summary: str

    opportunities: list[dict[str, Any]]
    selected_opportunity: dict[str, Any]

    prd_draft: dict[str, Any]
    evaluation_report: dict[str, Any]

    needs_review: bool
    human_review_status: str
    review_reason: str
    review_notes: list[str]

    bi_metrics: dict[str, Any]
    product_review_summary: str

    errors: list[dict[str, Any]]
    current_step: str
    persistence_result: dict[str, Any]
    export_result: dict[str, Any]


def add_error(state: ResearchState, step: str, message: str) -> ResearchState:
    errors = state.setdefault("errors", [])
    errors.append({"step": step, "message": message})
    return state
