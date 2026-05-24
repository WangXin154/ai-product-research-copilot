from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


TOPIC_RULES = {
    "reliability": ["bug", "error", "crash", "fail", "broken", "exception", "traceback"],
    "performance": ["slow", "latency", "performance", "timeout", "memory", "speed"],
    "documentation": ["doc", "docs", "documentation", "example", "tutorial", "guide"],
    "data_upload": ["upload", "file", "csv", "dataframe", "dataset"],
    "setup": ["install", "dependency", "version", "environment", "setup", "python"],
    "integration": ["api", "integration", "connection", "connect", "sql", "database"],
    "usability": ["confusing", "difficult", "ux", "ui", "workflow", "experience"],
}

TOPIC_PAIN_TEXT = {
    "reliability": ("用户在使用过程中遇到错误、崩溃或失败，影响产品稳定性。", "用户需要更稳定的运行体验和更清晰的错误提示。"),
    "performance": ("用户反馈性能、延迟或资源占用问题，影响使用效率。", "用户需要更快的响应速度和更可预测的性能表现。"),
    "documentation": ("用户难以通过文档和示例理解正确用法。", "用户需要更清晰、可执行、版本一致的文档和示例。"),
    "data_upload": ("用户在文件上传、数据处理或表格交互中遇到阻碍。", "用户需要更稳定的数据导入体验和更明确的数据处理反馈。"),
    "setup": ("用户在安装、依赖和环境配置上遇到问题。", "用户需要更简单的安装流程和更清楚的环境兼容说明。"),
    "integration": ("用户在 API、数据库或外部系统集成中遇到问题。", "用户需要更可靠的集成能力和更完整的连接说明。"),
    "usability": ("用户反馈流程复杂或体验不直观。", "用户需要更低学习成本和更顺滑的产品操作路径。"),
    "other": ("用户反馈中存在尚未归类但值得关注的问题。", "用户需要产品团队进一步归纳和验证该类需求。"),
}


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def infer_topic(text: str, feedback_type: str | None = None) -> str:
    lowered = text.lower()
    if feedback_type == "bug":
        return "reliability"
    for topic, keywords in TOPIC_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return topic
    return "other"


def severity_for_feedback(feedback: dict[str, Any], topic: str) -> int:
    feedback_type = feedback.get("feedback_type")
    if feedback_type == "bug" or topic == "reliability":
        return 4
    if feedback_type == "complaint":
        return 4
    if topic in {"performance", "integration", "setup"}:
        return 3
    return 2


def feedback_analyst_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "feedback_analyst_node"
    feedback_rows = state.get("cleaned_feedback", [])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    topics: list[dict[str, Any]] = []

    for row in feedback_rows:
        text = row.get("cleaned_text", "")
        topic = infer_topic(text, row.get("feedback_type"))
        severity = severity_for_feedback(row, topic)
        evidence_quote = text[:280]
        grouped[topic].append({**row, "topic": topic, "severity": severity, "evidence_quote": evidence_quote})
        topics.append(
            {
                "topic_id": f"topic_{topic}_{stable_id(row.get('feedback_id', ''))}",
                "feedback_id": row.get("feedback_id"),
                "repo_name": row.get("repo_name"),
                "topic": topic,
                "sentiment": "negative" if row.get("feedback_type") in {"bug", "complaint"} else "neutral",
                "severity": severity,
                "evidence_quote": evidence_quote,
                "confidence": 0.75,
            }
        )

    pain_points: list[dict[str, Any]] = []
    for topic, rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True):
        user_pain, user_need = TOPIC_PAIN_TEXT.get(topic, TOPIC_PAIN_TEXT["other"])
        evidence_quotes = [row["evidence_quote"] for row in rows[:5]]
        related_feedback_ids = [row.get("feedback_id") for row in rows[:20]]
        avg_severity = round(sum(row["severity"] for row in rows) / max(1, len(rows)), 2)
        pain_points.append(
            {
                "pain_point_id": f"pp_{topic}",
                "topic": topic,
                "user_pain": user_pain,
                "user_need": user_need,
                "evidence_count": len(rows),
                "severity": avg_severity,
                "priority_hint": "P0" if len(rows) >= 20 or avg_severity >= 4 else "P1",
                "evidence_quotes": evidence_quotes,
                "related_feedback_ids": related_feedback_ids,
            }
        )

    state["topics"] = topics
    state["pain_points"] = pain_points
    return state

