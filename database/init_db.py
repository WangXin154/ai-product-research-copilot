from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = PROJECT_ROOT / "database" / "product_research.db"
SCHEMA_PATH = PROJECT_ROOT / "database" / "schema.sql"


def init_db(db_path: Path = DEFAULT_DB_PATH, schema_path: Path = SCHEMA_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_sql = schema_path.read_text(encoding="utf-8")

    with sqlite3.connect(db_path) as conn:
        conn.executescript(schema_sql)
        conn.commit()

    return db_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize the product research SQLite database.")
    parser.add_argument("--db", default=str(DEFAULT_DB_PATH), help="SQLite database path.")
    parser.add_argument("--schema", default=str(SCHEMA_PATH), help="Schema SQL path.")
    args = parser.parse_args()

    db_path = init_db(Path(args.db), Path(args.schema))
    print(f"Database initialized: {db_path}")


if __name__ == "__main__":
    main()

