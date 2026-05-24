from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


def bi_insight_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "bi_insight_node"
    feedback_summary = state.get("feedback_summary", {})
    opportunities = state.get("opportunities", [])
    evaluation_report = state.get("evaluation_report", {})

    priority_counts = {"P0": 0, "P1": 0, "P2": 0, "Backlog": 0}
    for opportunity in opportunities:
        priority = opportunity.get("priority", "Backlog")
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    avg_priority_score = 0.0
    if opportunities:
        avg_priority_score = round(sum(item["priority_score"] for item in opportunities) / len(opportunities), 2)

    bi_metrics = {
        "feedback_count": feedback_summary.get("feedback_count", 0),
        "repo_count": feedback_summary.get("repo_count", 0),
        "comment_count": feedback_summary.get("comment_count", 0),
        "topic_count": len(state.get("topics", [])),
        "pain_point_count": len(state.get("pain_points", [])),
        "opportunity_count": len(opportunities),
        "p0_count": priority_counts.get("P0", 0),
        "p1_count": priority_counts.get("P1", 0),
        "p2_count": priority_counts.get("P2", 0),
        "backlog_count": priority_counts.get("Backlog", 0),
        "avg_priority_score": avg_priority_score,
        "evidence_coverage": evaluation_report.get("evidence_coverage"),
        "hallucination_risk": evaluation_report.get("hallucination_risk"),
        "prd_completeness": evaluation_report.get("prd_completeness"),
        "overall_score": evaluation_report.get("overall_score"),
    }

    selected = state.get("selected_opportunity", {})
    summary = (
        f"本次工作流分析了 {bi_metrics['feedback_count']} 条清洗反馈，覆盖 {bi_metrics['repo_count']} 个仓库，"
        f"识别出 {bi_metrics['pain_point_count']} 个痛点和 {bi_metrics['opportunity_count']} 个机会点。"
    )
    if selected:
        summary += f" 当前优先推荐机会点为：{selected.get('opportunity_name')}，优先级 {selected.get('priority')}。"
    if evaluation_report:
        summary += (
            f" PRD 评估总分为 {evaluation_report.get('overall_score')}，"
            f"幻觉风险为 {evaluation_report.get('hallucination_risk')}。"
        )

    state["bi_metrics"] = bi_metrics
    state["product_review_summary"] = summary
    return state

