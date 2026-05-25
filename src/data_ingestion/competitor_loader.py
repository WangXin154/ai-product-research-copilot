from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import insert_records


DEFAULT_COMPETITOR_FILE = PROJECT_ROOT / "data" / "sample_competitors.csv"


def stable_id(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_competitor_csv(file_path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            competitor_name = (row.get("competitor_name") or "").strip()
            feature_name = (row.get("feature_name") or "").strip()
            if not competitor_name or not feature_name:
                continue
            records.append(
                {
                    "competitor_id": row.get("competitor_id") or f"cmp_{stable_id(competitor_name)}",
                    "competitor_name": competitor_name,
                    "feature_name": feature_name,
                    "feature_category": (row.get("feature_category") or "").strip(),
                    "coverage": (row.get("coverage") or "unknown").strip().lower(),
                    "strength": (row.get("strength") or "").strip(),
                    "weakness": (row.get("weakness") or "").strip(),
                    "source_url": (row.get("source_url") or "").strip(),
                    "created_at": now_iso(),
                }
            )
    return records


def load_competitors(file_path: Path = DEFAULT_COMPETITOR_FILE) -> dict[str, Any]:
    records = load_competitor_csv(file_path)
    result = insert_records("competitor_features", records)
    return {
        "success": result.get("success", False),
        "file_path": str(file_path),
        "records_seen": len(records),
        "insert_result": result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Load competitor feature matrix into competitor_features.")
    parser.add_argument("--file", default=str(DEFAULT_COMPETITOR_FILE), help="CSV file path.")
    args = parser.parse_args()

    result = load_competitors(Path(args.file))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
