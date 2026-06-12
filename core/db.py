import os
import sqlite3
from contextlib import contextmanager

from config import config


SCHEMA = """
CREATE TABLE IF NOT EXISTS expenses (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    item       TEXT    NOT NULL,
    type       TEXT    NOT NULL,
    cost       REAL    NOT NULL,           -- signed: income positive, expense negative
    week       INTEGER NOT NULL,           -- 0 = fixed monthly, 1..n = calendar week
    month      TEXT    NOT NULL,           -- 'YYYY-MM'
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_expenses_month ON expenses(month);

CREATE TABLE IF NOT EXISTS fixed_expenses (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    item     TEXT NOT NULL,
    type     TEXT NOT NULL,
    cost     REAL NOT NULL,
    position INTEGER
);

CREATE TABLE IF NOT EXISTS defaults (
    item     TEXT PRIMARY KEY,             -- lowercased merchant/item name
    type     TEXT NOT NULL,
    position INTEGER
);

CREATE TABLE IF NOT EXISTS categories (
    type     TEXT PRIMARY KEY,
    bucket   TEXT,                          -- which budget bucket; NULL = not budgeted
    position INTEGER
);

CREATE TABLE IF NOT EXISTS budget (
    category TEXT PRIMARY KEY,
    amount   REAL NOT NULL,
    position INTEGER
);
"""


def connect() -> sqlite3.Connection:
    db_dir = os.path.dirname(config.db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    conn = sqlite3.connect(config.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")   # bot + web API can share the file
    conn.execute("PRAGMA busy_timeout=5000")  # wait out the other process's writes
    return conn


@contextmanager
def get_conn():
    conn = connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _migrate_category_bucket(conn) -> None:
    """Add categories.bucket to pre-existing DBs and backfill from the old rules."""
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(categories)")]
    if "bucket" in cols:
        return
    conn.execute("ALTER TABLE categories ADD COLUMN bucket TEXT")
    for r in conn.execute("SELECT type FROM categories").fetchall():
        t = r["type"].strip()
        if t.startswith("Bill"):
            b = "Bills"
        elif t == "Groceries":
            b = "Groceries"
        elif t in ("Income", "Tax"):
            b = None
        else:
            b = "Everyday Spending"
        conn.execute("UPDATE categories SET bucket = ? WHERE type = ?", (b, r["type"]))


def _migrate_positions(conn) -> None:
    """Add a `position` column to settings tables on older DBs, seeded from current order."""
    for table in ("categories", "budget", "defaults", "fixed_expenses"):
        cols = [r["name"] for r in conn.execute(f"PRAGMA table_info({table})")]
        if "position" not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN position INTEGER")
            conn.execute(f"UPDATE {table} SET position = rowid")


def init_db() -> None:
    """Create tables if they don't exist. Safe to call on every startup."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        _migrate_category_bucket(conn)
        _migrate_positions(conn)
