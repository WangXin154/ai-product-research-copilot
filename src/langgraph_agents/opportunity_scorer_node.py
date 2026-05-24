from __future__ import annotations

import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState


def clamp(value: float, low: float = 1.0, high: float = 5.0) -> float:
    return max(low, min(high, value))


def priority_from_score(score: float) -> str:
    if score >= 4.0:
        return "P0"
    if score >= 3.0:
        return "P1"
    if score >= 2.0:
        return "P2"
    return "Backlog"


def opportunity_scorer_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "opportunity_scorer_node"
    opportunities: list[dict[str, Any]] = []

    for pain_point in state.get("pain_points", []):
        evidence_count = float(pain_point.get("evidence_count", 0))
        severity = float(pain_point.get("severity", 2))

        user_value = clamp(2.5 + evidence_count / 20)
        business_value = 4.0
        frequency = clamp(1 + evidence_count / 15)
        effort = 3.0
        risk = 2.0
        ai_feasibility = 4.0
        evidence_strength = clamp(1 + evidence_count / 10)

        priority_score = (
            user_value * 0.25
            + business_value * 0.20
            + frequency * 0.15
            + severity * 0.15
            + ai_feasibility * 0.10
            + evidence_strength * 0.15
            - effort * 0.15
            - risk * 0.10
        )
        priority_score = round(priority_score, 2)

        opportunities.append(
            {
                "opportunity_id": f"opp_{pain_point['topic']}",
                "pain_point_ids": [pain_point["pain_point_id"]],
                "opportunity_name": f"优化{pain_point['topic']}相关用户体验",
                "topic": pain_point["topic"],
                "user_value": round(user_value, 2),
                "business_value": business_value,
                "frequency": round(frequency, 2),
                "severity": severity,
                "effort": effort,
                "risk": risk,
                "ai_feasibility": ai_feasibility,
                "evidence_strength": round(evidence_strength, 2),
                "priority_score": priority_score,
                "priority": priority_from_score(priority_score),
                "source_pain_point": pain_point,
            }
        )

    opportunities.sort(key=lambda item: item["priority_score"], reverse=True)
    state["opportunities"] = opportunities
    state["selected_opportunity"] = opportunities[0] if opportunities else {}
    return state

