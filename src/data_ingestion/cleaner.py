from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import insert_records, query


CODE_BLOCK_RE = re.compile(r"```.*?```", re.DOTALL)
INLINE_CODE_RE = re.compile(r"`([^`]*)`")
URL_RE = re.compile(r"https?://\S+")
HTML_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def stable_id(*parts: Any) -> str:
    raw = "::".join("" if part is None else str(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def clean_text(title: str, body: str) -> str:
    text = f"{title or ''}\n\n{body or ''}".strip()
    text = CODE_BLOCK_RE.sub(" ", text)
    text = INLINE_CODE_RE.sub(r"\1", text)
    text = URL_RE.sub(" ", text)
    text = HTML_RE.sub(" ", text)
    text = text.replace("#", " ").replace("*", " ").replace("_", " ")
    text = WHITESPACE_RE.sub(" ", text)
    return text.strip()


def detect_language(text: str) -> str:
    cjk_count = sum(1 for char in text if "\u4e00" <= char <= "\u9fff")
    if cjk_count >= 3:
        return "zh"
    return "en"


def infer_feedback_type(title: str, body: str, labels_json: str) -> str:
    text = f"{title} {body}".lower()
    try:
        labels = " ".join(json.loads(labels_json or "[]")).lower()
    except json.JSONDecodeError:
        labels = labels_json.lower()

    combined = f"{text} {labels}"
    if any(keyword in combined for keyword in ["bug", "error", "crash", "fail", "broken", "exception"]):
        return "bug"
    if any(keyword in combined for keyword in ["feature", "enhancement", "request", "support", "add"]):
        return "feature_request"
    if any(keyword in combined for keyword in ["confusing", "difficult", "slow", "annoying", "frustrating"]):
        return "complaint"
    if "?" in combined or any(keyword in combined for keyword in ["how to", "question", "help"]):
        return "question"
    if any(keyword in combined for keyword in ["great", "thanks", "love", "awesome"]):
        return "praise"
    return "other"


def build_cleaned_records(limit: int | None = None) -> list[dict[str, Any]]:
    sql = """
        SELECT rf.*
        FROM raw_feedback rf
        LEFT JOIN cleaned_feedback cf ON rf.feedback_id = cf.feedback_id
        WHERE cf.feedback_id IS NULL
        ORDER BY rf.created_at DESC
    """
    if limit:
        sql += f" LIMIT {int(limit)}"

    rows = query(sql)["data"]
    seen_text_hashes: set[str] = set()
    records: list[dict[str, Any]] = []

    for row in rows:
        cleaned_text = clean_text(row.get("title") or "", row.get("body") or "")
        text_hash = hashlib.sha1(cleaned_text.lower().encode("utf-8")).hexdigest()
        duplicate_flag = 1 if text_hash in seen_text_hashes else 0
        seen_text_hashes.add(text_hash)

        noise_flag = 1 if len(cleaned_text) < 20 else 0
        if not cleaned_text:
            noise_flag = 1

        records.append(
            {
                "cleaned_id": stable_id("cleaned", row["feedback_id"]),
                "feedback_id": row["feedback_id"],
                "cleaned_text": cleaned_text,
                "language": detect_language(cleaned_text),
                "feedback_type": infer_feedback_type(row.get("title") or "", row.get("body") or "", row.get("labels") or "[]"),
                "duplicate_flag": duplicate_flag,
                "noise_flag": noise_flag,
            }
        )

    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean raw_feedback into cleaned_feedback.")
    parser.add_argument("--limit", type=int, default=0, help="Max rows to clean. 0 means all new rows.")
    args = parser.parse_args()

    records = build_cleaned_records(limit=args.limit or None)
    result = insert_records("cleaned_feedback", records)
    print(json.dumps({"cleaned_feedback": result, "records_seen": len(records)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

