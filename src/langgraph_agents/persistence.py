from __future__ import annotations

import json
import sqlite3
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState
from src.mcp_tools.database_tool import insert_records
from src.utils.config import DATABASE_PATH


DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "outputs" / "workflow"

FEEDBACK_TOPIC_EXTRA_COLUMNS = {
    "repo_name": "TEXT",
    "topic_keywords": "TEXT",
    "topic_summary": "TEXT",
    "user_need": "TEXT",
    "cluster_id": "TEXT",
    "evidence_count": "INTEGER DEFAULT 1",
    "analysis_method": "TEXT",
}


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_feedback_topics_schema() -> None:
    with sqlite3.connect(DATABASE_PATH) as conn:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(feedback_topics)").fetchall()}
        for column, column_type in FEEDBACK_TOPIC_EXTRA_COLUMNS.items():
            if column not in existing:
                conn.execute(f"ALTER TABLE feedback_topics ADD COLUMN {column} {column_type}")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_topics_repo ON feedback_topics(repo_name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_topics_cluster ON feedback_topics(cluster_id)")
        conn.commit()


def save_topics(state: ResearchState) -> int:
    topics = state.get("topics", [])
    if not topics:
        return 0
    ensure_feedback_topics_schema()
    records = []
    for topic in topics:
        records.append(
            {
                "topic_id": topic.get("topic_id"),
                "feedback_id": topic.get("feedback_id"),
                "repo_name": topic.get("repo_name"),
                "topic": topic.get("topic", "Other Product Feedback"),
                "topic_keywords": topic.get("topic_keywords", "[]"),
                "topic_summary": topic.get("topic_summary", ""),
                "user_need": topic.get("user_need", ""),
                "cluster_id": topic.get("cluster_id", ""),
                "evidence_count": int(topic.get("evidence_count", 1)),
                "sentiment": topic.get("sentiment", "neutral"),
                "severity": int(topic.get("severity", 2)),
                "evidence_quote": topic.get("evidence_quote", ""),
                "confidence": float(topic.get("confidence", 0.5)),
                "analysis_method": topic.get("analysis_method", "embedding_llm"),
                "created_at": now_iso(),
            }
        )
    insert_records("feedback_topics", records)
    return len(records)


def save_pain_points(state: ResearchState) -> int:
    records = []
    for pain_point in state.get("pain_points", []):
        records.append(
            {
                "pain_point_id": pain_point.get("pain_point_id"),
                "topic_id": None,
                "user_pain": pain_point.get("user_pain", ""),
                "user_need": pain_point.get("user_need", ""),
                "evidence_count": int(pain_point.get("evidence_count", 0)),
                "priority_hint": pain_point.get("priority_hint", ""),
                "related_feedback_ids": json_dumps(pain_point.get("related_feedback_ids", [])),
                "created_at": now_iso(),
            }
        )
    if records:
        insert_records("pain_points", records)
    return len(records)


def save_opportunities(state: ResearchState) -> int:
    records = []
    for opportunity in state.get("opportunities", []):
        records.append(
            {
                "opportunity_id": opportunity.get("opportunity_id"),
                "pain_point_ids": json_dumps(opportunity.get("pain_point_ids", [])),
                "opportunity_name": opportunity.get("opportunity_name", ""),
                "user_value": opportunity.get("user_value"),
                "business_value": opportunity.get("business_value"),
                "frequency": opportunity.get("frequency"),
                "severity": opportunity.get("severity"),
                "effort": opportunity.get("effort"),
                "risk": opportunity.get("risk"),
                "ai_feasibility": opportunity.get("ai_feasibility"),
                "evidence_strength": opportunity.get("evidence_strength"),
                "priority_score": opportunity.get("priority_score"),
                "priority": opportunity.get("priority"),
                "created_at": now_iso(),
            }
        )
    if records:
        insert_records("opportunity_scores", records)
    return len(records)


def save_prd_draft(state: ResearchState) -> int:
    prd = state.get("prd_draft", {})
    if not prd:
        return 0
    opportunity_id = prd.get("opportunity_id") or state.get("selected_opportunity", {}).get("opportunity_id")
    prd_id = f"prd_{opportunity_id or state.get('project_id', 'demo_project')}"
    record = {
        "prd_id": prd_id,
        "opportunity_id": opportunity_id,
        "title": prd.get("title", ""),
        "background": prd.get("background", ""),
        "user_story": prd.get("user_story", ""),
        "requirements": json_dumps(prd.get("requirements", [])),
        "non_functional_requirements": json_dumps(["保留原始证据链接", "输出结构稳定，便于评估和导出"]),
        "acceptance_criteria": json_dumps(prd.get("acceptance_criteria", [])),
        "metrics": json_dumps(prd.get("metrics", [])),
        "risks": json_dumps(prd.get("risks", [])),
        "evidence_refs": json_dumps(prd.get("evidence_refs", [])),
        "status": prd.get("status", "draft"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    insert_records("prd_drafts", [record])
    state["prd_draft"]["prd_id"] = prd_id
    return 1


def save_evaluation_report(state: ResearchState) -> int:
    report = state.get("evaluation_report", {})
    if not report:
        return 0
    record = {
        "evaluation_id": report.get("evaluation_id"),
        "output_id": report.get("output_id") or state.get("prd_draft", {}).get("prd_id", ""),
        "output_type": report.get("output_type", "prd"),
        "relevance": report.get("relevance"),
        "accuracy": report.get("accuracy"),
        "actionability": report.get("actionability"),
        "evidence_coverage": report.get("evidence_coverage"),
        "hallucination_risk": report.get("hallucination_risk"),
        "human_edit_rate": report.get("human_edit_rate"),
        "prd_completeness": report.get("prd_completeness"),
        "overall_score": report.get("overall_score"),
        "evaluation_notes": report.get("evaluation_notes"),
        "created_at": report.get("created_at") or now_iso(),
    }
    insert_records("ai_evaluation_results", [record])
    return 1


def save_bi_metrics(state: ResearchState) -> int:
    metrics = state.get("bi_metrics", {})
    if not metrics:
        return 0
    today = date.today().isoformat()
    records = []
    for metric_name, metric_value in metrics.items():
        if isinstance(metric_value, (int, float)) and metric_value is not None:
            records.append(
                {
                    "metric_id": f"{today}_{state.get('project_id', 'demo_project')}_{metric_name}",
                    "date": today,
                    "metric_name": metric_name,
                    "metric_value": float(metric_value),
                    "product_area": "workflow",
                    "repo_name": "all",
                    "dimension": state.get("project_id", "demo_project"),
                    "created_at": now_iso(),
                }
            )
    if records:
        insert_records("bi_metrics_daily", records)
    return len(records)


def save_workflow_results(state: ResearchState) -> dict[str, Any]:
    result = {
        "success": True,
        "topics_saved": save_topics(state),
        "pain_points_saved": save_pain_points(state),
        "opportunities_saved": save_opportunities(state),
        "prd_saved": save_prd_draft(state),
        "evaluation_saved": save_evaluation_report(state),
        "bi_metrics_saved": save_bi_metrics(state),
    }
    state["persistence_result"] = result
    return result


def build_export_payload(state: ResearchState) -> dict[str, Any]:
    selected_opportunity = state.get("selected_opportunity", {})
    evaluation_report = state.get("evaluation_report", {})
    prd_draft = state.get("prd_draft", {})
    return {
        "project_id": state.get("project_id"),
        "project_name": state.get("project_name"),
        "feedback_summary": state.get("feedback_summary", {}),
        "top_topics": state.get("topics", [])[:10],
        "top_pain_points": state.get("pain_points", [])[:5],
        "competitor_matrix": state.get("competitor_matrix", [])[:10],
        "differentiation_opportunities": state.get("differentiation_opportunities", [])[:10],
        "competitor_review_summary": state.get("competitor_review_summary", ""),
        "selected_opportunity": {
            "opportunity_id": selected_opportunity.get("opportunity_id"),
            "opportunity_name": selected_opportunity.get("opportunity_name"),
            "priority": selected_opportunity.get("priority"),
            "priority_score": selected_opportunity.get("priority_score"),
        },
        "prd_draft": {
            "prd_id": prd_draft.get("prd_id"),
            "title": prd_draft.get("title"),
            "status": prd_draft.get("status"),
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
        "errors": state.get("errors", []),
    }


def build_workflow_markdown(payload: dict[str, Any]) -> str:
    feedback = payload.get("feedback_summary", {})
    opportunity = payload.get("selected_opportunity", {})
    evaluation = payload.get("evaluation_report", {})
    human_review = payload.get("human_review", {})
    bi_metrics = payload.get("bi_metrics", {})
    pain_points = payload.get("top_pain_points", [])
    topics = payload.get("top_topics", [])
    competitor_matrix = payload.get("competitor_matrix", [])
    differentiation_opportunities = payload.get("differentiation_opportunities", [])

    lines = [
        "# AI 产品调研 Agent 工作流运行摘要",
        "",
        "## 数据概况",
        "",
        f"- 分析反馈数：{feedback.get('feedback_count', 0)}",
        f"- 覆盖仓库数：{feedback.get('repo_count', 0)}",
        f"- Comments 数：{feedback.get('comment_count', 0)}",
        "",
        "## AI 发现的主题",
        "",
    ]
    for topic in topics[:5]:
        lines.extend(
            [
                f"### {topic.get('topic')}",
                "",
                f"- 情绪：{topic.get('sentiment')}",
                f"- 置信度：{topic.get('confidence')}",
                f"- 聚类证据数：{topic.get('evidence_count')}",
                f"- 摘要：{topic.get('topic_summary')}",
                "",
            ]
        )

    lines.extend(["## 高频痛点", ""])
    for pain_point in pain_points:
        lines.extend(
            [
                f"### {pain_point.get('topic')}",
                "",
                f"- 用户痛点：{pain_point.get('user_pain')}",
                f"- 用户需求：{pain_point.get('user_need')}",
                f"- 证据数量：{pain_point.get('evidence_count')}",
                "",
            ]
        )

    lines.extend(["## 竞品能力矩阵", ""])
    if competitor_matrix:
        for item in competitor_matrix[:6]:
            lines.extend(
                [
                    f"### {item.get('feature_category')}",
                    "",
                    f"- 目标能力：{item.get('target_capability')}",
                    f"- 覆盖竞品数：{item.get('competitor_count')}",
                    f"- 平均覆盖分：{item.get('avg_coverage_score')}",
                    "",
                ]
            )
    else:
        lines.extend(["尚未加载竞品功能数据。", ""])

    lines.extend(["## 差异化机会", ""])
    for item in differentiation_opportunities[:5]:
        lines.extend(
            [
                f"- {item.get('opportunity_name')}：{item.get('suggested_action')}",
            ]
        )
    if not differentiation_opportunities:
        lines.append("- 暂无差异化机会，请先加载竞品功能数据。")
    lines.append("")

    lines.extend(
        [
            "## 推荐机会点",
            "",
            f"- 名称：{opportunity.get('opportunity_name')}",
            f"- 优先级：{opportunity.get('priority')}",
            f"- 评分：{opportunity.get('priority_score')}",
            "",
            "## AI Evaluation",
            "",
            f"- 总评分：{evaluation.get('overall_score')}",
            f"- 证据覆盖率：{evaluation.get('evidence_coverage')}",
            f"- 幻觉风险：{evaluation.get('hallucination_risk')}",
            f"- PRD 完整度：{evaluation.get('prd_completeness')}",
            "",
            "## Human Review Gate",
            "",
            f"- 是否需要人工审核：{human_review.get('needs_review')}",
            f"- 审核状态：{human_review.get('human_review_status')}",
            f"- 审核原因：{human_review.get('review_reason')}",
            "",
        ]
    )
    for note in human_review.get("review_notes", []):
        lines.append(f"- {note}")
    lines.extend(
        [
            "",
            "## BI 指标",
            "",
        ]
    )
    for metric_name, metric_value in bi_metrics.items():
        lines.append(f"- {metric_name}: {metric_value}")

    lines.extend(["", "## 产品复盘建议", "", payload.get("product_review_summary", "")])
    return "\n".join(lines)


def export_workflow_results(state: ResearchState, output_dir: Path | str = DEFAULT_OUTPUT_DIR) -> dict[str, Any]:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    payload = build_export_payload(state)
    prd_markdown = state.get("prd_draft", {}).get("markdown", "")
    bi_metrics = state.get("bi_metrics", {})

    summary_json_path = output_path / "workflow_summary.json"
    summary_md_path = output_path / "workflow_summary.md"
    prd_path = output_path / "prd_draft.md"
    bi_metrics_path = output_path / "bi_metrics.json"

    summary_json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_md_path.write_text(build_workflow_markdown(payload), encoding="utf-8")
    prd_path.write_text(prd_markdown, encoding="utf-8")
    bi_metrics_path.write_text(json.dumps(bi_metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "success": True,
        "output_dir": str(output_path),
        "files": {
            "workflow_summary_json": str(summary_json_path),
            "workflow_summary_md": str(summary_md_path),
            "prd_draft_md": str(prd_path),
            "bi_metrics_json": str(bi_metrics_path),
        },
    }
    state["export_result"] = result
    return result
