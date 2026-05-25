from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from langgraph.graph import END, StateGraph


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.bi_insight_node import bi_insight_node
from src.langgraph_agents.collector_node import collector_node
from src.langgraph_agents.competitor_analyst_node import competitor_analyst_node
from src.langgraph_agents.evaluation_node import evaluation_node
from src.langgraph_agents.feedback_analyst_node import feedback_analyst_node
from src.langgraph_agents.human_review_node import human_review_node
from src.langgraph_agents.opportunity_scorer_node import opportunity_scorer_node
from src.langgraph_agents.persistence import export_workflow_results, save_workflow_results
from src.langgraph_agents.prd_writer_node import prd_writer_node
from src.langgraph_agents.state import ResearchState, add_error


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def safe_node(node_func):
    def wrapped(state: ResearchState) -> ResearchState:
        try:
            return node_func(state)
        except Exception as error:
            add_error(state, node_func.__name__, str(error))
            return state

    return wrapped


def route_after_collector(state: ResearchState) -> str:
    if state.get("errors"):
        return "end"
    if not state.get("cleaned_feedback"):
        add_error(state, "collector_node", "No cleaned feedback was found for the selected repos.")
        return "end"
    return "continue"


def route_after_opportunity_scorer(state: ResearchState) -> str:
    if state.get("errors"):
        return "bi_insight"
    if not state.get("opportunities"):
        return "bi_insight"
    return "prd_writer"


def route_after_evaluation(state: ResearchState) -> str:
    report = state.get("evaluation_report", {})
    hallucination_risk = report.get("hallucination_risk")
    evidence_coverage = float(report.get("evidence_coverage") or 0)
    overall_score = float(report.get("overall_score") or 0)
    if hallucination_risk == "high" or evidence_coverage < 0.6 or overall_score < 4.0:
        return "human_review"
    return "bi_insight"


def build_langgraph_workflow():
    workflow = StateGraph(ResearchState)

    workflow.add_node("collector", safe_node(collector_node))
    workflow.add_node("feedback_analyst", safe_node(feedback_analyst_node))
    workflow.add_node("competitor_analyst", safe_node(competitor_analyst_node))
    workflow.add_node("opportunity_scorer", safe_node(opportunity_scorer_node))
    workflow.add_node("prd_writer", safe_node(prd_writer_node))
    workflow.add_node("evaluation", safe_node(evaluation_node))
    workflow.add_node("human_review", safe_node(human_review_node))
    workflow.add_node("bi_insight", safe_node(bi_insight_node))

    workflow.set_entry_point("collector")
    workflow.add_conditional_edges("collector", route_after_collector, {"continue": "feedback_analyst", "end": END})
    workflow.add_edge("feedback_analyst", "competitor_analyst")
    workflow.add_edge("competitor_analyst", "opportunity_scorer")
    workflow.add_conditional_edges(
        "opportunity_scorer",
        route_after_opportunity_scorer,
        {"prd_writer": "prd_writer", "bi_insight": "bi_insight"},
    )
    workflow.add_edge("prd_writer", "evaluation")
    workflow.add_conditional_edges(
        "evaluation",
        route_after_evaluation,
        {"human_review": "human_review", "bi_insight": "bi_insight"},
    )
    workflow.add_edge("human_review", "bi_insight")
    workflow.add_edge("bi_insight", END)
    return workflow.compile()


def build_initial_state(selected_repos: list[str], limit: int = 100) -> ResearchState:
    return {
        "project_id": "demo_project",
        "project_name": "AI Product Research Agent MVP",
        "selected_repos": selected_repos,
        "limit": limit,
        "errors": [],
    }


def run_research_workflow(selected_repos: list[str], limit: int = 100) -> ResearchState:
    app = build_langgraph_workflow()
    initial_state = build_initial_state(selected_repos, limit)
    return app.invoke(initial_state)


def build_summary(state: ResearchState) -> dict:
    selected_opportunity = state.get("selected_opportunity", {})
    prd_draft = state.get("prd_draft", {})
    evaluation_report = state.get("evaluation_report", {})
    return {
        "project_id": state.get("project_id"),
        "feedback_summary": state.get("feedback_summary", {}),
        "topic_count": len({item.get("topic") for item in state.get("topics", []) if item.get("topic")}),
        "pain_point_count": len(state.get("pain_points", [])),
        "competitor_category_count": len(state.get("competitor_matrix", [])),
        "differentiation_opportunity_count": len(state.get("differentiation_opportunities", [])),
        "opportunity_count": len(state.get("opportunities", [])),
        "top_topics": state.get("topics", [])[:3],
        "top_pain_points": state.get("pain_points", [])[:3],
        "competitor_review_summary": state.get("competitor_review_summary", ""),
        "top_differentiation_opportunities": state.get("differentiation_opportunities", [])[:3],
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
        "human_review": {
            "needs_review": state.get("needs_review", False),
            "human_review_status": state.get("human_review_status", ""),
            "review_reason": state.get("review_reason", ""),
            "review_notes": state.get("review_notes", []),
        },
        "bi_metrics": state.get("bi_metrics", {}),
        "product_review_summary": state.get("product_review_summary", ""),
        "persistence_result": state.get("persistence_result", {}),
        "export_result": state.get("export_result", {}),
        "errors": state.get("errors", []),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the MVP product research workflow.")
    parser.add_argument("--repos", nargs="*", default=[], help="Repos to analyze. If omitted, use all cleaned feedback.")
    parser.add_argument("--limit", type=int, default=100, help="Max cleaned feedback rows per repo.")
    parser.add_argument("--save", action="store_true", help="Save workflow results to database tables.")
    parser.add_argument("--export", action="store_true", help="Export workflow summary files.")
    parser.add_argument("--output-dir", default=str(PROJECT_ROOT / "outputs" / "workflow"), help="Workflow export directory.")
    args = parser.parse_args()

    state = run_research_workflow(args.repos, args.limit)
    if args.save:
        save_workflow_results(state)
    if args.export:
        export_workflow_results(state, args.output_dir)
    print(json.dumps(build_summary(state), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
