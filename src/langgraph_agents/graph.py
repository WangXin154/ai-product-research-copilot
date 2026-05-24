from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.bi_insight_node import bi_insight_node
from src.langgraph_agents.collector_node import collector_node
from src.langgraph_agents.evaluation_node import evaluation_node
from src.langgraph_agents.feedback_analyst_node import feedback_analyst_node
from src.langgraph_agents.opportunity_scorer_node import opportunity_scorer_node
from src.langgraph_agents.prd_writer_node import prd_writer_node
from src.langgraph_agents.state import ResearchState, add_error


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def run_research_workflow(selected_repos: list[str], limit: int = 100) -> ResearchState:
    state: ResearchState = {
        "project_id": "demo_project",
        "project_name": "AI Product Research Agent MVP",
        "selected_repos": selected_repos,
        "limit": limit,
        "errors": [],
    }

    nodes = [
        collector_node,
        feedback_analyst_node,
        opportunity_scorer_node,
        prd_writer_node,
        evaluation_node,
        bi_insight_node,
    ]

    for node in nodes:
        try:
            state = node(state)
        except Exception as error:  # Keep the MVP workflow observable instead of failing silently.
            add_error(state, node.__name__, str(error))
            break

    return state


def build_summary(state: ResearchState) -> dict:
    selected_opportunity = state.get("selected_opportunity", {})
    prd_draft = state.get("prd_draft", {})
    evaluation_report = state.get("evaluation_report", {})
    return {
        "project_id": state.get("project_id"),
        "feedback_summary": state.get("feedback_summary", {}),
        "pain_point_count": len(state.get("pain_points", [])),
        "opportunity_count": len(state.get("opportunities", [])),
        "top_pain_points": state.get("pain_points", [])[:3],
        "selected_opportunity": {
            "opportunity_id": selected_opportunity.get("opportunity_id"),
            "opportunity_name": selected_opportunity.get("opportunity_name"),
            "priority": selected_opportunity.get("priority"),
            "priority_score": selected_opportunity.get("priority_score"),
        },
        "prd_draft": {
            "title": prd_draft.get("title"),
            "status": prd_draft.get("status"),
            "markdown_preview": prd_draft.get("markdown", "")[:1000],
        },
        "evaluation_report": {
            "overall_score": evaluation_report.get("overall_score"),
            "hallucination_risk": evaluation_report.get("hallucination_risk"),
            "evidence_coverage": evaluation_report.get("evidence_coverage"),
            "prd_completeness": evaluation_report.get("prd_completeness"),
        },
        "bi_metrics": state.get("bi_metrics", {}),
        "product_review_summary": state.get("product_review_summary", ""),
        "errors": state.get("errors", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MVP product research workflow.")
    parser.add_argument("--repos", nargs="*", default=[], help="Repos to analyze. If omitted, use all cleaned feedback.")
    parser.add_argument("--limit", type=int, default=100, help="Max cleaned feedback rows per repo.")
    args = parser.parse_args()

    state = run_research_workflow(args.repos, args.limit)
    print(json.dumps(build_summary(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
