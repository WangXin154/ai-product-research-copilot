from __future__ import annotations

import importlib
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


CORE_TABLES = [
    "raw_feedback",
    "cleaned_feedback",
    "feedback_topics",
    "pain_points",
    "competitor_features",
    "opportunity_scores",
    "prd_drafts",
    "ai_evaluation_results",
    "bi_metrics_daily",
]

REQUIRED_FILES = [
    "README.md",
    "requirements.txt",
    ".env.example",
    "docs/PRD.md",
    "docs/langgraph_workflow.md",
    "docs/mcp_tool_design.md",
    "docs/metrics_framework.md",
    "docs/data_schema.md",
    "docs/case_study.md",
    "database/schema.sql",
    "database/init_db.py",
    "src/data_ingestion/github_api.py",
    "src/data_ingestion/cleaner.py",
    "src/data_ingestion/validate_collection.py",
    "src/data_ingestion/competitor_loader.py",
    "src/langgraph_agents/graph.py",
    "src/langgraph_agents/human_review_node.py",
    "src/langgraph_agents/topic_clusterer.py",
    "src/mcp_server/server.py",
    "app/streamlit_app.py",
]

REQUIRED_OUTPUTS = [
    "outputs/workflow/workflow_summary.json",
    "outputs/workflow/workflow_summary.md",
    "outputs/workflow/prd_draft.md",
    "outputs/workflow/bi_metrics.json",
]

REQUIRED_REQUIREMENTS = [
    "streamlit",
    "pandas",
    "plotly",
    "python-dotenv",
    "openai",
    "langgraph",
    "mcp",
]

IMPORT_CHECKS = [
    "src.langgraph_agents.graph",
    "src.langgraph_agents.human_review_node",
    "src.langgraph_agents.topic_clusterer",
    "src.mcp_server.server",
    "src.mcp_tools.database_tool",
    "src.mcp_tools.evaluation_tool",
    "src.mcp_tools.export_tool",
    "src.mcp_tools.github_tool",
]


def check_file(path: str) -> bool:
    return (PROJECT_ROOT / path).exists()


def load_requirements() -> set[str]:
    path = PROJECT_ROOT / "requirements.txt"
    if not path.exists():
        return set()
    packages = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        value = line.strip().lstrip("\ufeff")
        if not value or value.startswith("#"):
            continue
        packages.add(value.split("==")[0].split(">=")[0].split("<=")[0].lower())
    return packages


def database_counts(db_path: Path) -> tuple[dict[str, int], list[str]]:
    if not db_path.exists():
        return {}, CORE_TABLES[:]
    counts: dict[str, int] = {}
    missing: list[str] = []
    with sqlite3.connect(db_path) as conn:
        existing_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
        }
        for table in CORE_TABLES:
            if table not in existing_tables:
                missing.append(table)
                continue
            counts[table] = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    return counts, missing


def import_modules() -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for module_name in IMPORT_CHECKS:
        try:
            importlib.import_module(module_name)
            results[module_name] = {"success": True, "error": ""}
        except Exception as error:
            results[module_name] = {"success": False, "error": str(error)}
    return results


def main() -> None:
    db_path = PROJECT_ROOT / "database" / "product_research.db"
    table_counts, missing_tables = database_counts(db_path)
    requirements = load_requirements()
    imports = import_modules()

    files = {path: check_file(path) for path in REQUIRED_FILES}
    outputs = {path: check_file(path) for path in REQUIRED_OUTPUTS}
    requirement_checks = {name: name in requirements for name in REQUIRED_REQUIREMENTS}

    checks = {
        "database_exists": db_path.exists(),
        "all_core_tables_exist": not missing_tables,
        "has_raw_feedback": table_counts.get("raw_feedback", 0) > 0,
        "has_cleaned_feedback": table_counts.get("cleaned_feedback", 0) > 0,
        "has_feedback_topics": table_counts.get("feedback_topics", 0) > 0,
        "has_competitor_features": table_counts.get("competitor_features", 0) > 0,
        "has_prd_drafts": table_counts.get("prd_drafts", 0) > 0,
        "has_ai_evaluation_results": table_counts.get("ai_evaluation_results", 0) > 0,
        "required_files_exist": all(files.values()),
        "workflow_outputs_exist": all(outputs.values()),
        "requirements_complete": all(requirement_checks.values()),
        "imports_ok": all(item["success"] for item in imports.values()),
    }

    payload = {
        "success": all(checks.values()),
        "project_root": str(PROJECT_ROOT),
        "checks": checks,
        "table_counts": table_counts,
        "missing_tables": missing_tables,
        "missing_files": [path for path, exists in files.items() if not exists],
        "missing_outputs": [path for path, exists in outputs.items() if not exists],
        "missing_requirements": [name for name, exists in requirement_checks.items() if not exists],
        "import_results": imports,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))

    if not payload["success"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
