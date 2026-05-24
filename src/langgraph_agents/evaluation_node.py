from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.langgraph_agents.state import ResearchState
from src.mcp_tools.evaluation_tool import score_output


def evaluation_node(state: ResearchState) -> ResearchState:
    state["current_step"] = "evaluation_node"
    prd_draft = state.get("prd_draft", {})
    if not prd_draft:
        state["evaluation_report"] = {}
        return state

    result = score_output(
        {
            "output_id": prd_draft.get("opportunity_id"),
            "output_type": "prd",
            "output_text": prd_draft.get("markdown", ""),
            "evidence_texts": prd_draft.get("evidence_refs", []),
            "save_to_db": False,
        }
    )
    state["evaluation_report"] = result["data"]
    return state

