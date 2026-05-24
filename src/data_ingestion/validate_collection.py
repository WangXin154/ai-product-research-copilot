from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.config import DATABASE_PATH


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


def fetch_all(conn: sqlite3.Connection, sql: str) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql).fetchall()
    return [dict(row) for row in rows]


def fetch_one_value(conn: sqlite3.Connection, sql: str) -> Any:
    return conn.execute(sql).fetchone()[0]


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for table in CORE_TABLES:
        counts[table] = int(fetch_one_value(conn, f"SELECT COUNT(*) FROM {table}"))
    return counts


def build_report(db_path: Path, sample_limit: int) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        counts = table_counts(conn)
        raw_count = counts["raw_feedback"]
        cleaned_count = counts["cleaned_feedback"]

        repo_counts = fetch_all(
            conn,
            """
            SELECT repo_name, COUNT(*) AS feedback_count
            FROM raw_feedback
            GROUP BY repo_name
            ORDER BY feedback_count DESC
            """,
        )

        comment_counts_by_repo = fetch_all(
            conn,
            """
            SELECT repo_name, COUNT(*) AS comment_count
            FROM raw_feedback
            WHERE comment_id IS NOT NULL AND LENGTH(comment_id) > 0
            GROUP BY repo_name
            ORDER BY comment_count DESC
            """,
        )

        feedback_types = fetch_all(
            conn,
            """
            SELECT feedback_type, COUNT(*) AS feedback_count
            FROM cleaned_feedback
            GROUP BY feedback_type
            ORDER BY feedback_count DESC
            """,
        )

        samples = fetch_all(
            conn,
            f"""
            SELECT
                repo_name,
                issue_id,
                comment_id,
                title,
                substr(body, 1, 160) AS body_preview,
                url
            FROM raw_feedback
            ORDER BY fetched_at DESC
            LIMIT {int(sample_limit)}
            """,
        )

        missing_url_count = int(
            fetch_one_value(
                conn,
                """
                SELECT COUNT(*)
                FROM raw_feedback
                WHERE url IS NULL OR LENGTH(url) = 0
                """,
            )
        )

        missing_issue_id_count = int(
            fetch_one_value(
                conn,
                """
                SELECT COUNT(*)
                FROM raw_feedback
                WHERE issue_id IS NULL OR LENGTH(issue_id) = 0
                """,
            )
        )

        comments_total = int(
            fetch_one_value(
                conn,
                """
                SELECT COUNT(*)
                FROM raw_feedback
                WHERE comment_id IS NOT NULL AND LENGTH(comment_id) > 0
                """,
            )
        )

        clean_coverage = 0.0 if raw_count == 0 else round(cleaned_count / raw_count, 4)

    checks = {
        "database_exists": db_path.exists(),
        "has_raw_feedback": raw_count > 0,
        "has_cleaned_feedback": cleaned_count > 0,
        "cleaned_matches_raw": raw_count == cleaned_count,
        "has_repo_name_issue_id_url": missing_url_count == 0 and missing_issue_id_count == 0,
        "has_comments": comments_total > 0,
    }

    return {
        "db_path": str(db_path),
        "table_counts": counts,
        "repo_counts": repo_counts,
        "comment_counts_by_repo": comment_counts_by_repo,
        "feedback_types": feedback_types,
        "quality": {
            "comments_total": comments_total,
            "missing_url_count": missing_url_count,
            "missing_issue_id_count": missing_issue_id_count,
            "clean_coverage": clean_coverage,
        },
        "checks": checks,
        "samples": samples,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate GitHub collection quality for the data layer.")
    parser.add_argument("--db", default=str(DATABASE_PATH), help="SQLite database path.")
    parser.add_argument("--sample-limit", type=int, default=5, help="Number of raw feedback samples to print.")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}. Run python database/init_db.py first.")

    report = build_report(db_path, args.sample_limit)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
