from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState
from src.mcp_tools.database_tool import query


COVERAGE_SCORE = {
    "high": 3,
    "medium": 2,
    "low": 1,
    "none": 0,
    "unknown": 0,
}

TARGET_CAPABILITIES = {
    "feedback_analysis": "将真实用户反馈转化为结构化洞察",
    "topic_discovery": "通过 embedding / LLM 聚类发现高频主题",
    "agent_workflow": "用多节点 Agent 工作流串联调研到 PRD",
    "prd_generation": "自动生成带证据引用的 PRD 草稿",
    "ai_evaluation": "评估 AI 输出相关性、准确性、证据覆盖率和幻觉风险",
    "bi_dashboard": "用 BI Dashboard 复盘反馈、机会点和 AI 质量",
    "human_review": "对高风险输出进入人工审核",
    "export": "导出 PRD、调研报告、CSV、JSON 和作品集材料",
}


def normalize_category(value: str) -> str:
    value = (value or "").strip().lower()
    aliases = {
        "feedback analysis": "feedback_analysis",
        "topic discovery": "topic_discovery",
        "agent workflow": "agent_workflow",
        "prd generation": "prd_generation",
        "ai evaluation": "ai_evaluation",
        "bi dashboard": "bi_dashboard",
        "dashboard": "bi_dashboard",
        "human review": "human_review",
        "export": "export",
    }
    return aliases.get(value, value.replace(" ", "_").replace("-", "_"))


def fetch_competitor_features() -> list[dict[str, Any]]:
    sql = """
        SELECT
            competitor_id,
            competitor_name,
            feature_name,
            feature_category,
            coverage,
            strength,
            weakness,
            source_url
        FROM competitor_features
        ORDER BY feature_category, competitor_name, feature_name
    """
    return query(sql)["data"]


def build_competitor_matrix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_category: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        category = normalize_category(row.get("feature_category", "unknown"))
        by_category[category].append(row)

    matrix: list[dict[str, Any]] = []
    for category, items in sorted(by_category.items()):
        competitor_cells = []
        for item in items:
            coverage = (item.get("coverage") or "unknown").lower()
            competitor_cells.append(
                {
                    "competitor_name": item.get("competitor_name"),
                    "feature_name": item.get("feature_name"),
                    "coverage": coverage,
                    "coverage_score": COVERAGE_SCORE.get(coverage, 0),
                    "strength": item.get("strength", ""),
                    "weakness": item.get("weakness", ""),
                    "source_url": item.get("source_url", ""),
                }
            )
        avg_score = round(sum(cell["coverage_score"] for cell in competitor_cells) / max(1, len(competitor_cells)), 2)
        matrix.append(
            {
                "feature_category": category,
                "target_capability": TARGET_CAPABILITIES.get(category, "该能力与产品调研平台相关。"),
                "competitor_count": len({cell["competitor_name"] for cell in competitor_cells}),
                "avg_coverage_score": avg_score,
                "competitors": competitor_cells,
            }
        )
    return matrix


def build_differentiation_opportunities(matrix: list[dict[str, Any]]) -> list[dict[str, Any]]:
    opportunities: list[dict[str, Any]] = []
    for item in matrix:
        category = item.get("feature_category", "")
        avg_score = float(item.get("avg_coverage_score", 0))
        competitors = item.get("competitors", [])
        weak_points = [cell.get("weakness", "") for cell in competitors if cell.get("weakness")]
        if avg_score < 2.4 or category in {"ai_evaluation", "prd_generation", "human_review", "bi_dashboard"}:
            opportunities.append(
                {
                    "category": category,
                    "opportunity_name": f"强化 {category} 差异化能力",
                    "rationale": TARGET_CAPABILITIES.get(category, "该能力可用于形成产品差异化。"),
                    "competitor_gap": "；".join(weak_points[:3]) or "竞品在该能力上覆盖不完整或不够产品化。",
                    "suggested_action": "将该能力与真实反馈、证据引用、AI 评估和 Dashboard 复盘打通。",
                    "priority_hint": "P1" if category in {"ai_evaluation", "prd_generation", "bi_dashboard"} else "P2",
                }
            )
    return opportunities


def summarize_competitor_insights(matrix: list[dict[str, Any]], opportunities: list[dict[str, Any]]) -> str:
    if not matrix:
        return "当前尚未加载竞品功能数据，建议先运行 competitor_loader.py。"
    top_categories = ", ".join(item.get("feature_category", "") for item in matrix[:5])
    return (
        f"本次竞品分析覆盖 {len(matrix)} 类能力，重点能力包括 {top_categories}。"
        f" 系统识别出 {len(opportunities)} 个差异化机会，建议优先围绕 AI Evaluation、PRD Generation、BI Dashboard 和 Human Review 建立作品集亮点。"
    )


def competitor_analyst_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "competitor_analyst_node"
    rows = fetch_competitor_features()
    matrix = build_competitor_matrix(rows)
    opportunities = build_differentiation_opportunities(matrix)

    state["competitor_features"] = rows
    state["competitor_matrix"] = matrix
    state["competitor_insights"] = opportunities
    state["differentiation_opportunities"] = opportunities
    state["competitor_review_summary"] = summarize_competitor_insights(matrix, opportunities)
    return state
