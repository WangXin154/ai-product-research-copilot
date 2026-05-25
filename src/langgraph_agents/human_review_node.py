from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


def build_review_notes(evaluation_report: dict[str, Any], prd_draft: dict[str, Any]) -> list[str]:
    notes: list[str] = []
    hallucination_risk = evaluation_report.get("hallucination_risk")
    evidence_coverage = float(evaluation_report.get("evidence_coverage") or 0)
    overall_score = float(evaluation_report.get("overall_score") or 0)

    if hallucination_risk == "high":
        notes.append("幻觉风险为 high，需要人工检查 PRD 中是否存在缺少证据支撑的结论。")
    if evidence_coverage < 0.6:
        notes.append(f"证据覆盖率为 {evidence_coverage:.2f}，低于 0.60，建议补充更多原始反馈引用。")
    if overall_score < 4.0:
        notes.append(f"AI 输出总分为 {overall_score:.2f}，低于 4.0，建议人工复核后再进入作品集展示。")

    evidence_refs = prd_draft.get("evidence_refs", [])
    if not evidence_refs:
        notes.append("PRD 未检测到 evidence_refs，建议补充可追溯的 Issue / Comment 证据。")

    if not notes:
        notes.append("AI 输出质量达到当前阈值，可进入 BI 复盘和导出流程。")
    return notes


def human_review_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "human_review_node"
    evaluation_report = state.get("evaluation_report", {})
    prd_draft = state.get("prd_draft", {})

    hallucination_risk = evaluation_report.get("hallucination_risk", "unknown")
    evidence_coverage = float(evaluation_report.get("evidence_coverage") or 0)
    overall_score = float(evaluation_report.get("overall_score") or 0)

    needs_review = hallucination_risk == "high" or evidence_coverage < 0.6 or overall_score < 4.0
    review_notes = build_review_notes(evaluation_report, prd_draft)

    if needs_review:
        review_status = "needs_review"
        review_reason = "AI 输出存在高风险或证据覆盖不足，需要人工复核。"
    else:
        review_status = "approved_for_export"
        review_reason = "AI 输出通过当前质量阈值，可进入导出和 BI 复盘。"

    state["needs_review"] = needs_review
    state["human_review_status"] = review_status
    state["review_reason"] = review_reason
    state["review_notes"] = review_notes
    return state
