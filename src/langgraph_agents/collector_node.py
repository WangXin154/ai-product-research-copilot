from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState
from src.mcp_tools.database_tool import get_cleaned_feedback


def collector_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "collector_node"
    selected_repos = state.get("selected_repos", [])
    limit = int(state.get("limit", 100))

    collected: list[dict[str, Any]] = []
    if selected_repos:
        per_repo_limit = max(1, limit)
        for repo_name in selected_repos:
            result = get_cleaned_feedback(repo_name=repo_name, limit=per_repo_limit)
            collected.extend(result["data"])
    else:
        result = get_cleaned_feedback(limit=limit)
        collected.extend(result["data"])

    repo_counter = Counter(row.get("repo_name", "unknown") for row in collected)
    type_counter = Counter(row.get("feedback_type", "unknown") for row in collected)
    comment_count = sum(1 for row in collected if row.get("comment_id"))

    state["cleaned_feedback"] = collected
    state["feedback_summary"] = {
        "feedback_count": len(collected),
        "repo_count": len(repo_counter),
        "comment_count": comment_count,
        "repo_distribution": dict(repo_counter),
        "feedback_type_distribution": dict(type_counter),
    }
    return state

