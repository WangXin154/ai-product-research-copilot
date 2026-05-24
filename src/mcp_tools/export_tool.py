from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.mcp_tools.database_tool import get_cleaned_feedback, get_comment_summary, get_repo_summary, query


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


OUTPUT_ROOT = PROJECT_ROOT / "outputs"


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def export_cleaned_feedback_csv(input_data: dict[str, Any]) -> dict[str, Any]:
    repo_name = input_data.get("repo_name")
    limit = int(input_data.get("limit", 1000))
    output_dir = ensure_output_dir(Path(input_data.get("output_dir", OUTPUT_ROOT / "exports")))
    rows = get_cleaned_feedback(repo_name=repo_name, limit=limit)["data"]
    file_path = output_dir / "cleaned_feedback.csv"

    fieldnames = [
        "cleaned_id",
        "feedback_id",
        "repo_name",
        "issue_id",
        "comment_id",
        "feedback_type",
        "language",
        "cleaned_text",
        "url",
    ]
    with file_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})

    return {"success": True, "tool": "export.cleaned_feedback_csv", "file_path": str(file_path), "row_count": len(rows)}


def export_repo_summary_json(input_data: dict[str, Any]) -> dict[str, Any]:
    output_dir = ensure_output_dir(Path(input_data.get("output_dir", OUTPUT_ROOT / "exports")))
    payload = {
        "generated_at": datetime.now().isoformat(),
        "repo_summary": get_repo_summary()["data"],
        "comment_summary": get_comment_summary()["data"],
    }
    file_path = output_dir / "repo_summary.json"
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"success": True, "tool": "export.repo_summary_json", "file_path": str(file_path)}


def export_research_summary_markdown(input_data: dict[str, Any]) -> dict[str, Any]:
    output_dir = ensure_output_dir(Path(input_data.get("output_dir", OUTPUT_ROOT / "exports")))
    repo_summary = get_repo_summary()["data"]
    feedback_types = query(
        """
        SELECT feedback_type, COUNT(*) AS feedback_count
        FROM cleaned_feedback
        GROUP BY feedback_type
        ORDER BY feedback_count DESC
        """
    )["data"]

    lines = [
        "# AI 产品调研数据采集摘要",
        "",
        f"生成时间：{datetime.now().isoformat()}",
        "",
        "## 仓库反馈数量",
        "",
        "| 仓库 | Issues | Comments | 总反馈 |",
        "|---|---:|---:|---:|",
    ]
    for row in repo_summary:
        lines.append(f"| {row['repo_name']} | {row['issue_count']} | {row['comment_count']} | {row['feedback_count']} |")

    lines.extend(["", "## 反馈类型分布", "", "| 类型 | 数量 |", "|---|---:|"])
    for row in feedback_types:
        lines.append(f"| {row['feedback_type']} | {row['feedback_count']} |")

    file_path = output_dir / "research_summary.md"
    file_path.write_text("\n".join(lines), encoding="utf-8")
    return {"success": True, "tool": "export.research_summary_markdown", "file_path": str(file_path)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export product research data.")
    parser.add_argument("--cleaned-csv", action="store_true", help="Export cleaned feedback CSV.")
    parser.add_argument("--repo-summary", action="store_true", help="Export repo summary JSON.")
    parser.add_argument("--markdown", action="store_true", help="Export markdown research summary.")
    parser.add_argument("--output-dir", default=str(OUTPUT_ROOT / "exports"))
    args = parser.parse_args()

    results = []
    payload = {"output_dir": args.output_dir}
    if args.cleaned_csv:
        results.append(export_cleaned_feedback_csv(payload))
    if args.repo_summary:
        results.append(export_repo_summary_json(payload))
    if args.markdown:
        results.append(export_research_summary_markdown(payload))
    if not results:
        parser.print_help()
        return

    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
