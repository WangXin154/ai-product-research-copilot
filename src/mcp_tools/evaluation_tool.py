from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import insert_records


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


PRD_REQUIRED_SECTIONS = [
    "背景",
    "用户故事",
    "功能需求",
    "验收标准",
    "成功指标",
    "风险",
]


def stable_id(*parts: Any) -> str:
    raw = "::".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def split_claims(output_text: str) -> list[str]:
    candidates = re.split(r"[\n。.!?；;]+", output_text)
    return [candidate.strip() for candidate in candidates if len(candidate.strip()) >= 12]


def token_set(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9_\u4e00-\u9fff]+", text.lower()))


def is_supported_by_evidence(claim: str, evidence_texts: list[str]) -> bool:
    claim_tokens = token_set(claim)
    if not claim_tokens:
        return False
    for evidence in evidence_texts:
        evidence_tokens = token_set(evidence)
        overlap = claim_tokens & evidence_tokens
        if len(overlap) >= max(2, min(5, len(claim_tokens) // 4)):
            return True
    return False


def calculate_evidence_coverage(output_text: str, evidence_texts: list[str]) -> dict[str, Any]:
    claims = split_claims(output_text)
    if not claims:
        return {"coverage": 0.0, "supported_claims": 0, "total_claims": 0, "unsupported_claims": []}

    supported = []
    unsupported = []
    for claim in claims:
        if is_supported_by_evidence(claim, evidence_texts):
            supported.append(claim)
        else:
            unsupported.append(claim)

    return {
        "coverage": round(len(supported) / len(claims), 4),
        "supported_claims": len(supported),
        "total_claims": len(claims),
        "unsupported_claims": unsupported[:10],
    }


def calculate_prd_completeness(output_text: str) -> float:
    if not output_text.strip():
        return 0.0
    matched = sum(1 for section in PRD_REQUIRED_SECTIONS if section in output_text)
    return round((matched / len(PRD_REQUIRED_SECTIONS)) * 5, 2)


def score_output(input_data: dict[str, Any]) -> dict[str, Any]:
    output_id = input_data.get("output_id") or stable_id("output", input_data.get("output_text", ""))
    output_type = input_data.get("output_type", "prd")
    output_text = input_data.get("output_text", "")
    evidence_texts = input_data.get("evidence_texts", [])

    evidence_result = calculate_evidence_coverage(output_text, evidence_texts)
    prd_completeness = calculate_prd_completeness(output_text) if output_type == "prd" else None
    evidence_coverage = evidence_result["coverage"]

    hallucination_risk = "low"
    if evidence_coverage < 0.5:
        hallucination_risk = "high"
    elif evidence_coverage < 0.8:
        hallucination_risk = "medium"

    relevance = 4.0 if evidence_texts else 3.0
    accuracy = round(3.0 + min(evidence_coverage * 2, 2.0), 2)
    actionability = 4.0 if any(keyword in output_text for keyword in ["验收标准", "成功指标", "下一步", "需求"]) else 3.0
    completeness_score = prd_completeness if prd_completeness is not None else 4.0
    overall_score = round((relevance + accuracy + actionability + completeness_score) / 4, 2)

    data = {
        "evaluation_id": stable_id("evaluation", output_id, datetime.now(timezone.utc).isoformat()),
        "output_id": output_id,
        "output_type": output_type,
        "relevance": relevance,
        "accuracy": accuracy,
        "actionability": actionability,
        "evidence_coverage": evidence_coverage,
        "hallucination_risk": hallucination_risk,
        "human_edit_rate": input_data.get("human_edit_rate"),
        "prd_completeness": prd_completeness,
        "overall_score": overall_score,
        "evaluation_notes": json.dumps(evidence_result, ensure_ascii=False),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    save_to_db = bool(input_data.get("save_to_db", False))
    insert_result = insert_records("ai_evaluation_results", [data]) if save_to_db else None

    return {
        "success": True,
        "tool": "evaluation.score_output",
        "data": data,
        "evidence_result": evidence_result,
        "insert_result": insert_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rule-based AI evaluation tool.")
    parser.add_argument("--text", default="", help="Output text to evaluate.")
    parser.add_argument("--evidence", nargs="*", default=[], help="Evidence texts.")
    parser.add_argument("--save", action="store_true", help="Save evaluation result to database.")
    args = parser.parse_args()

    result = score_output({"output_text": args.text, "evidence_texts": args.evidence, "save_to_db": args.save})
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
