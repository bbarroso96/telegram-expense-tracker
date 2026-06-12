"""Seed the SQLite database with starter config (and optionally demo expenses).

Usage:
    python -m core.seed          # config only (fresh start, no expenses)
    python -m core.seed --demo   # also add a few current-week sample expenses

Re-running is safe: each config table is only seeded when it's empty, so your
own edits made later (via the website's Settings) are never clobbered.
"""
import sys

from dotenv import load_dotenv

load_dotenv()

from core.db import init_db, get_conn
from core.repository import append_expense, ensure_month


# (type, bucket) — bucket is which budget the category counts toward (None = not budgeted)
CATEGORIES = [
    ("Food", "Everyday Spending"), ("Groceries", "Groceries"),
    ("Leasure", "Everyday Spending"), ("Other", "Everyday Spending"),
    ("Bill - Internet and Phone", "Bills"), ("Bill - Rent", "Bills"),
    ("Bill - Parking", "Bills"), ("Bill - Health Insurance", "Bills"),
    ("Bill - Streaming", "Bills"), ("Bill - Gas", "Bills"),
    ("Tax", None), ("Income", None),
]

BUDGET = [
    ("Bills", 3000.0),
    ("Groceries", 1000.0),
    ("Everyday Spending", 1000.0),
]

DEFAULTS = [
    ("costco", "Groceries"), ("target", "Groceries"), ("amazon", "Other"),
    ("gas", "Bill - Gas"), ("parking", "Bill - Parking"), ("movie", "Leasure"),
]

FIXED = [
    ("Internet and Phone", "Bill - Internet and Phone", -60.0),
    ("Rent", "Bill - Rent", -1200.0),
    ("Parking", "Bill - Parking", -100.0),
    ("Health Insurance", "Bill - Health Insurance", -250.0),
    ("Streaming", "Bill - Streaming", -15.0),
    ("Salary", "Income", 4000.0),
    ("Side Income", "Income", 500.0),
    ("Income Tax", "Tax", -600.0),
]

# (item, type, amount) — added to the current week when --demo is passed
DEMO_EXPENSES = [
    ("Costco", "Groceries", 115.0),
    ("Coffee", "Food", 4.50),
    ("Gas", "Bill - Gas", 36.0),
    ("Movie", "Leasure", 24.0),
]


def _seed_if_empty(conn, table: str, sql: str, rows: list) -> int:
    count = conn.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()["c"]
    if count:
        return 0
    conn.executemany(sql, rows)
    return len(rows)


def seed(demo: bool = False) -> None:
    init_db()
    with get_conn() as conn:
        added = {
            "categories": _seed_if_empty(
                conn, "categories", "INSERT INTO categories (type, bucket) VALUES (?, ?)",
                CATEGORIES,
            ),
            "budget": _seed_if_empty(
                conn, "budget", "INSERT INTO budget (category, amount) VALUES (?, ?)",
                BUDGET,
            ),
            "defaults": _seed_if_empty(
                conn, "defaults", "INSERT INTO defaults (item, type) VALUES (?, ?)",
                DEFAULTS,
            ),
            "fixed_expenses": _seed_if_empty(
                conn, "fixed_expenses",
                "INSERT INTO fixed_expenses (item, type, cost) VALUES (?, ?, ?)",
                FIXED,
            ),
        }

    # Materialize this month's fixed rows (week 0), like the old month sheet did.
    ensure_month()

    if demo:
        for item, type_, amount in DEMO_EXPENSES:
            append_expense(item, type_, amount)

    print("Seeded config tables:")
    for table, n in added.items():
        print(f"  {table}: {'+' + str(n) if n else 'already had data — skipped'}")
    if demo:
        print(f"Added {len(DEMO_EXPENSES)} demo expenses to the current week.")
    print("Done.")


if __name__ == "__main__":
    seed(demo="--demo" in sys.argv)
