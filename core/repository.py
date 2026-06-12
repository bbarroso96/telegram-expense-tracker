from datetime import date, timedelta

from core.db import get_conn


def current_week(today: date | None = None) -> int:
    """Returns the week number within the current month (Mon–Sun weeks)."""
    today = today or date.today()
    first_day = today.replace(day=1)
    first_monday = first_day - timedelta(days=first_day.weekday())
    return (today - first_monday).days // 7 + 1


def month_key(today: date | None = None) -> str:
    """Returns the current month as 'YYYY-MM'."""
    return (today or date.today()).strftime("%Y-%m")


def ensure_month(month: str | None = None) -> str:
    """Materialize fixed expenses as week-0 rows for a month the first time it's used.

    Mirrors the old behaviour where a new month sheet was pre-loaded with the
    fixed expenses. Idempotent: only seeds when the month has no rows yet.
    """
    month = month or month_key()
    with get_conn() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM expenses WHERE month = ?", (month,)
        ).fetchone()["c"]
        if count == 0:
            fixed = conn.execute(
                "SELECT item, type, cost FROM fixed_expenses ORDER BY position IS NULL, position, id"
            ).fetchall()
            for r in fixed:
                conn.execute(
                    "INSERT INTO expenses (item, type, cost, week, month) "
                    "VALUES (?, ?, ?, 0, ?)",
                    (r["item"], r["type"], float(r["cost"]), month),
                )
    return month


def _signed(type_: str, amount: float) -> float:
    """Income is stored positive; everything else negative."""
    return abs(amount) if type_.strip().lower() == "income" else -abs(amount)


def append_expense(item: str, type_: str, cost: float) -> int:
    """Appends an expense to the current week of the current month (used by the bot).
    Returns the week number."""
    week = current_week()
    add_expense(item, type_, cost, week)
    return week


def add_expense(item: str, type_: str, amount: float, week: int, month: str | None = None) -> int:
    """Adds an expense to a specific week/month (used by the web API). Returns its id."""
    month = ensure_month(month or month_key())
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO expenses (item, type, cost, week, month) VALUES (?, ?, ?, ?, ?)",
            (item, type_, _signed(type_, amount), week, month),
        )
        return cur.lastrowid


def update_expense(expense_id: int, item: str, type_: str, amount: float, week: int) -> int:
    """Updates an expense by id. Returns rows affected (0 if not found)."""
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE expenses SET item = ?, type = ?, cost = ?, week = ? WHERE id = ?",
            (item, type_, _signed(type_, amount), week, expense_id),
        )
        return cur.rowcount


def delete_expense(expense_id: int) -> int:
    """Deletes an expense by id. Returns rows affected (0 if not found)."""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cur.rowcount


def list_months() -> list:
    """Distinct months that have expenses, newest first ('YYYY-MM')."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT month FROM expenses ORDER BY month DESC"
        ).fetchall()
    return [r["month"] for r in rows]


def load_month_rows(month: str | None = None) -> list:
    """Like load_month_expenses but returns dicts with ids (for the web ledger)."""
    month = ensure_month(month or month_key())
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, item, week, type, cost FROM expenses WHERE month = ? ORDER BY week, id",
            (month,),
        ).fetchall()
    return [
        {"id": r["id"], "item": r["item"], "week": r["week"],
         "type": r["type"], "cost": float(r["cost"])}
        for r in rows
    ]


def load_defaults() -> dict:
    """Returns {item_lowercase: type} from the defaults table."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT item, type FROM defaults ORDER BY position IS NULL, position, rowid"
        ).fetchall()
    return {r["item"].strip().lower(): r["type"].strip() for r in rows if r["item"]}


def load_fixed_expenses() -> list:
    """Returns [(item, type, cost)] from the fixed_expenses table."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT item, type, cost FROM fixed_expenses ORDER BY position IS NULL, position, id"
        ).fetchall()
    return [(r["item"], r["type"], float(r["cost"])) for r in rows]


def load_categories() -> list:
    """Returns the list of category type strings (used by the bot keyboard / forms)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT type FROM categories ORDER BY position IS NULL, position, rowid"
        ).fetchall()
    return [r["type"] for r in rows if r["type"]]


def load_categories_full() -> list:
    """Returns [{type, bucket}] — each category with the budget bucket it counts toward."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT type, bucket FROM categories ORDER BY position IS NULL, position, rowid"
        ).fetchall()
    return [{"type": r["type"], "bucket": r["bucket"]} for r in rows if r["type"]]


def load_category_buckets() -> dict:
    """Returns {type: bucket} mapping (bucket None = not budgeted)."""
    with get_conn() as conn:
        rows = conn.execute("SELECT type, bucket FROM categories").fetchall()
    return {r["type"].strip(): r["bucket"] for r in rows if r["type"]}


def load_budget() -> dict:
    """Returns {category: budget_amount} from the budget table."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT category, amount FROM budget ORDER BY position IS NULL, position, rowid"
        ).fetchall()
    return {r["category"]: float(r["amount"]) for r in rows if r["category"]}


def load_month_expenses(month: str | None = None) -> list:
    """Returns [(item, week, type, cost)] for all rows in the given (default current) month."""
    month = ensure_month(month or month_key())
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT item, week, type, cost FROM expenses WHERE month = ? ORDER BY week, id",
            (month,),
        ).fetchall()
    return [(r["item"], r["week"], r["type"], float(r["cost"])) for r in rows]


# --- Settings CRUD (categories / budget / defaults / fixed) ---

def add_category(type_: str, bucket: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO categories (type, bucket) VALUES (?, ?)",
            (type_.strip(), bucket),
        )


def set_category_bucket(type_: str, bucket: str | None) -> None:
    """Assign which budget bucket a category counts toward (None = not budgeted)."""
    with get_conn() as conn:
        conn.execute("UPDATE categories SET bucket = ? WHERE type = ?", (bucket, type_.strip()))


def rename_category(old: str, new: str) -> None:
    """Rename a category everywhere it's referenced (categories, expenses, fixed, defaults)."""
    new = new.strip()
    with get_conn() as conn:
        conn.execute("UPDATE categories SET type = ? WHERE type = ?", (new, old))
        conn.execute("UPDATE expenses SET type = ? WHERE type = ?", (new, old))
        conn.execute("UPDATE fixed_expenses SET type = ? WHERE type = ?", (new, old))
        conn.execute("UPDATE defaults SET type = ? WHERE type = ?", (new, old))


def delete_category(type_: str) -> int:
    with get_conn() as conn:
        return conn.execute("DELETE FROM categories WHERE type = ?", (type_,)).rowcount


def set_budget(category: str, amount: float) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO budget (category, amount) VALUES (?, ?) "
            "ON CONFLICT(category) DO UPDATE SET amount = excluded.amount",
            (category.strip(), amount),
        )


def delete_budget(category: str) -> int:
    """Delete a budget bucket and unassign any categories that pointed to it."""
    with get_conn() as conn:
        conn.execute("UPDATE categories SET bucket = NULL WHERE bucket = ?", (category,))
        return conn.execute("DELETE FROM budget WHERE category = ?", (category,)).rowcount


def rename_budget(old: str, new: str) -> None:
    """Rename a budget bucket and repoint any categories assigned to it."""
    new = new.strip()
    with get_conn() as conn:
        conn.execute("UPDATE budget SET category = ? WHERE category = ?", (new, old))
        conn.execute("UPDATE categories SET bucket = ? WHERE bucket = ?", (new, old))


def set_default(item: str, type_: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO defaults (item, type) VALUES (?, ?) "
            "ON CONFLICT(item) DO UPDATE SET type = excluded.type",
            (item.strip().lower(), type_.strip()),
        )


def delete_default(item: str) -> int:
    with get_conn() as conn:
        return conn.execute(
            "DELETE FROM defaults WHERE item = ?", (item.strip().lower(),)
        ).rowcount


def load_fixed_rows() -> list:
    """Fixed monthly items with ids (for the Settings view)."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, item, type, cost FROM fixed_expenses ORDER BY position IS NULL, position, id"
        ).fetchall()
    return [
        {"id": r["id"], "item": r["item"], "type": r["type"], "cost": float(r["cost"])}
        for r in rows
    ]


def add_fixed(item: str, type_: str, cost: float) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO fixed_expenses (item, type, cost) VALUES (?, ?, ?)",
            (item, type_, cost),
        )
        return cur.lastrowid


def update_fixed(fixed_id: int, item: str, type_: str, cost: float) -> int:
    with get_conn() as conn:
        return conn.execute(
            "UPDATE fixed_expenses SET item = ?, type = ?, cost = ? WHERE id = ?",
            (item, type_, cost, fixed_id),
        ).rowcount


def delete_fixed(fixed_id: int) -> int:
    with get_conn() as conn:
        return conn.execute(
            "DELETE FROM fixed_expenses WHERE id = ?", (fixed_id,)
        ).rowcount


# --- Drag-and-drop reordering (positions follow the given key order) ---

def reorder_categories(order: list) -> None:
    with get_conn() as conn:
        for i, t in enumerate(order):
            conn.execute("UPDATE categories SET position = ? WHERE type = ?", (i, t))


def reorder_budget(order: list) -> None:
    with get_conn() as conn:
        for i, c in enumerate(order):
            conn.execute("UPDATE budget SET position = ? WHERE category = ?", (i, c))


def reorder_defaults(order: list) -> None:
    with get_conn() as conn:
        for i, item in enumerate(order):
            conn.execute(
                "UPDATE defaults SET position = ? WHERE item = ?", (i, item.strip().lower())
            )


def reorder_fixed(order: list) -> None:
    with get_conn() as conn:
        for i, fid in enumerate(order):
            conn.execute("UPDATE fixed_expenses SET position = ? WHERE id = ?", (i, fid))
