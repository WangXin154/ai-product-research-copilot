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


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_connection(db_path: Path = DATABASE_PATH) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def insert_records(table: str, records: list[dict[str, Any]], db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    if not records:
        return {"success": True, "inserted_count": 0, "failed_count": 0}

    keys = list(records[0].keys())
    placeholders = ", ".join(["?"] * len(keys))
    columns = ", ".join(keys)
    updates = ", ".join([f"{key}=excluded.{key}" for key in keys])
    sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders}) ON CONFLICT DO UPDATE SET {updates}"

    inserted_count = 0
    failed_count = 0

    with get_connection(db_path) as conn:
        for record in records:
            try:
                values = [record.get(key) for key in keys]
                conn.execute(sql, values)
                inserted_count += 1
            except sqlite3.Error:
                failed_count += 1
        conn.commit()

    return {"success": failed_count == 0, "inserted_count": inserted_count, "failed_count": failed_count}


def query(sql_query: str, params: tuple[Any, ...] = (), db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    with get_connection(db_path) as conn:
        rows = conn.execute(sql_query, params).fetchall()
    return {"success": True, "data": [dict(row) for row in rows]}


def get_raw_feedback(repo_name: str | None = None, limit: int = 20, db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT feedback_id, repo_name, issue_id, comment_id, title, body, labels, state, created_at, url
        FROM raw_feedback
    """
    params: list[Any] = []
    if repo_name:
        sql += " WHERE repo_name = ?"
        params.append(repo_name)
    sql += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    return query(sql, tuple(params), db_path)


def get_cleaned_feedback(repo_name: str | None = None, limit: int = 20, db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            cf.cleaned_id,
            cf.feedback_id,
            rf.repo_name,
            rf.issue_id,
            rf.comment_id,
            cf.feedback_type,
            cf.language,
            cf.cleaned_text,
            rf.url
        FROM cleaned_feedback cf
        JOIN raw_feedback rf ON cf.feedback_id = rf.feedback_id
    """
    params: list[Any] = []
    if repo_name:
        sql += " WHERE rf.repo_name = ?"
        params.append(repo_name)
    sql += " ORDER BY rf.created_at DESC LIMIT ?"
    params.append(limit)
    return query(sql, tuple(params), db_path)


def get_repo_summary(db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            repo_name,
            COUNT(*) AS feedback_count,
            SUM(CASE WHEN comment_id IS NOT NULL AND LENGTH(comment_id) > 0 THEN 1 ELSE 0 END) AS comment_count,
            SUM(CASE WHEN comment_id IS NULL OR LENGTH(comment_id) = 0 THEN 1 ELSE 0 END) AS issue_count,
            MIN(created_at) AS earliest_created_at,
            MAX(created_at) AS latest_created_at
        FROM raw_feedback
        GROUP BY repo_name
        ORDER BY feedback_count DESC
    """
    return query(sql, db_path=db_path)


def get_comment_summary(db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT repo_name, COUNT(*) AS comment_count
        FROM raw_feedback
        WHERE comment_id IS NOT NULL AND LENGTH(comment_id) > 0
        GROUP BY repo_name
        ORDER BY comment_count DESC
    """
    return query(sql, db_path=db_path)


def get_topic_summary(db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            topic,
            COUNT(*) AS feedback_count,
            ROUND(AVG(confidence), 4) AS avg_confidence,
            SUM(CASE WHEN sentiment = 'negative' THEN 1 ELSE 0 END) AS negative_count,
            SUM(CASE WHEN sentiment = 'positive' THEN 1 ELSE 0 END) AS positive_count,
            MAX(evidence_count) AS cluster_evidence_count
        FROM feedback_topics
        GROUP BY topic
        ORDER BY feedback_count DESC, avg_confidence DESC
    """
    return query(sql, db_path=db_path)


def get_topic_samples(limit: int = 10, db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            ft.topic,
            ft.repo_name,
            ft.sentiment,
            ft.confidence,
            ft.topic_keywords,
            ft.topic_summary,
            ft.user_need,
            substr(ft.evidence_quote, 1, 240) AS evidence_preview,
            rf.url
        FROM feedback_topics ft
        LEFT JOIN raw_feedback rf ON ft.feedback_id = rf.feedback_id
        ORDER BY ft.confidence DESC, ft.created_at DESC
        LIMIT ?
    """
    return query(sql, (limit,), db_path)


def get_competitor_summary(db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            competitor_name,
            COUNT(*) AS feature_count,
            SUM(CASE WHEN coverage = 'high' THEN 1 ELSE 0 END) AS high_coverage_count,
            SUM(CASE WHEN coverage = 'medium' THEN 1 ELSE 0 END) AS medium_coverage_count,
            SUM(CASE WHEN coverage = 'low' THEN 1 ELSE 0 END) AS low_coverage_count,
            GROUP_CONCAT(DISTINCT feature_category) AS feature_categories
        FROM competitor_features
        GROUP BY competitor_name
        ORDER BY feature_count DESC, competitor_name
    """
    return query(sql, db_path=db_path)


def get_competitor_matrix(db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT
            feature_category,
            feature_name,
            competitor_name,
            coverage,
            strength,
            weakness,
            source_url
        FROM competitor_features
        ORDER BY feature_category, feature_name, competitor_name
    """
    return query(sql, db_path=db_path)


def get_feedback_samples(limit: int = 5, include_comments: bool = True, db_path: Path = DATABASE_PATH) -> dict[str, Any]:
    sql = """
        SELECT repo_name, issue_id, comment_id, title, substr(body, 1, 240) AS body_preview, url
        FROM raw_feedback
    """
    if not include_comments:
        sql += " WHERE comment_id IS NULL OR LENGTH(comment_id) = 0"
    sql += " ORDER BY fetched_at DESC LIMIT ?"
    return query(sql, (limit,), db_path)


def table_counts(db_path: Path = DATABASE_PATH) -> dict[str, int]:
    tables = [
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
    counts: dict[str, int] = {}
    with get_connection(db_path) as conn:
        for table in tables:
            counts[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Database helper for product research data layer.")
    parser.add_argument("--stats", action="store_true", help="Print row counts for core tables.")
    parser.add_argument("--repo-summary", action="store_true", help="Print raw feedback counts by repo.")
    parser.add_argument("--comment-summary", action="store_true", help="Print comment counts by repo.")
    parser.add_argument("--topic-summary", action="store_true", help="Print AI-discovered topic summary.")
    parser.add_argument("--topic-samples", type=int, default=0, help="Print topic samples with evidence.")
    parser.add_argument("--competitor-summary", action="store_true", help="Print competitor feature coverage summary.")
    parser.add_argument("--competitor-matrix", action="store_true", help="Print competitor feature matrix rows.")
    parser.add_argument("--samples", type=int, default=0, help="Print raw feedback samples.")
    parser.add_argument("--db", default=str(DATABASE_PATH), help="SQLite database path.")
    args = parser.parse_args()

    if args.stats:
        print(json.dumps(table_counts(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.repo_summary:
        print(json.dumps(get_repo_summary(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.comment_summary:
        print(json.dumps(get_comment_summary(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.topic_summary:
        print(json.dumps(get_topic_summary(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.topic_samples:
        print(json.dumps(get_topic_samples(args.topic_samples, Path(args.db)), ensure_ascii=False, indent=2))
    elif args.competitor_summary:
        print(json.dumps(get_competitor_summary(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.competitor_matrix:
        print(json.dumps(get_competitor_matrix(Path(args.db)), ensure_ascii=False, indent=2))
    elif args.samples:
        print(json.dumps(get_feedback_samples(args.samples, db_path=Path(args.db)), ensure_ascii=False, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
