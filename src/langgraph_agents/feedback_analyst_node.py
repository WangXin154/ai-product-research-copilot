from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState
from src.langgraph_agents.topic_clusterer import build_embedding_topics


DEFAULT_PAIN_TEXT = (
    "用户在该主题下集中反馈了影响使用体验或任务完成效率的问题。",
    "用户需要产品团队给出更稳定、清晰、可执行的解决方案，并保留可追溯证据。",
)


def pain_text_from_topic(topic_rows: list[dict[str, Any]]) -> tuple[str, str]:
    if not topic_rows:
        return DEFAULT_PAIN_TEXT
    first = topic_rows[0]
    topic = first.get("topic", "该主题")
    summary = first.get("topic_summary") or DEFAULT_PAIN_TEXT[0]
    user_need = first.get("user_need") or DEFAULT_PAIN_TEXT[1]
    user_pain = f"用户围绕 {topic} 集中反馈：{summary}"
    return user_pain[:700], user_need[:700]


def feedback_analyst_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "feedback_analyst_node"
    feedback_rows = state.get("cleaned_feedback", [])

    topics = build_embedding_topics(feedback_rows)

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for topic_row in topics:
        grouped[topic_row.get("topic", "Other Product Feedback")].append(topic_row)

    pain_points: list[dict[str, Any]] = []
    for topic, rows in sorted(grouped.items(), key=lambda item: len(item[1]), reverse=True):
        user_pain, user_need = pain_text_from_topic(rows)
        evidence_quotes = [row.get("evidence_quote", "") for row in rows[:5] if row.get("evidence_quote")]
        related_feedback_ids = [row.get("feedback_id") for row in rows[:20] if row.get("feedback_id")]
        avg_severity = round(sum(float(row.get("severity", 2)) for row in rows) / max(1, len(rows)), 2)
        avg_confidence = round(sum(float(row.get("confidence", 0.5)) for row in rows) / max(1, len(rows)), 4)
        priority_hint = "P0" if len(rows) >= 20 or avg_severity >= 4 else "P1" if len(rows) >= 5 else "P2"
        pain_points.append(
            {
                "pain_point_id": f"pp_{topic.lower().replace(' ', '_').replace('/', '_')[:48]}",
                "topic": topic,
                "user_pain": user_pain,
                "user_need": user_need,
                "evidence_count": len(rows),
                "severity": avg_severity,
                "topic_confidence": avg_confidence,
                "priority_hint": priority_hint,
                "evidence_quotes": evidence_quotes,
                "related_feedback_ids": related_feedback_ids,
            }
        )

    state["topics"] = topics
    state["pain_points"] = pain_points
    return state
