import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.db import init_db
from core import repository as repo
from core.budget import compute_balance, savings_target
from api import schemas


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Budget Notebook API", lifespan=lifespan)

# Vite dev server runs on a different port; allow it during local development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/months")
def months():
    ms = repo.list_months()
    current = repo.month_key()
    if current not in ms:
        ms = [current] + ms
    return ms


@app.get("/api/summary")
def summary(month: str | None = None):
    month = month or repo.month_key()
    expenses = repo.load_month_expenses(month)
    budget = repo.load_budget()
    type_bucket = repo.load_category_buckets()
    balance = compute_balance(budget, expenses, type_bucket)

    buckets = [{"category": c, **d} for c, d in balance.items()]
    total_budget = sum(budget.values())
    total_spent = sum(d["spent"] for d in balance.values())
    income = sum(cost for _, _, _, cost in expenses if cost > 0)
    # Net of everything "not budgeted" (income + tax, signed) — drives the savings target.
    not_budgeted = sum(cost for _, _, t, cost in expenses if not type_bucket.get(t.strip()))
    weeks = sorted({w for _, w, _, _ in expenses if w > 0})

    # Savings target. While the month is ongoing it's protected at the budget
    # (deduct max(budget, spent) — overspending eats into it). Once the month
    # has ended, any unspent budget is banked, so we deduct actual spend.
    is_current = month == repo.month_key()
    savings = savings_target(not_budgeted, total_budget, total_spent, is_current)
    savings_basis = "budget" if (is_current and total_budget >= total_spent) else "spent"

    return {
        "month": month,
        "is_current": is_current,
        "buckets": buckets,
        "totals": {
            "budget": total_budget,
            "spent": total_spent,
            "remaining": total_budget - total_spent,
            "income": income,
            "not_budgeted": not_budgeted,
            "savings": savings,
            "savings_basis": savings_basis,
        },
        "weeks": weeks,
        "current_week": repo.current_week(),
    }


# --- Expenses ---

@app.get("/api/expenses")
def get_expenses(month: str | None = None):
    return repo.load_month_rows(month)


@app.post("/api/expenses", status_code=201)
def create_expense(e: schemas.ExpenseIn):
    return {"id": repo.add_expense(e.item, e.type, e.amount, e.week)}


@app.put("/api/expenses/{expense_id}")
def edit_expense(expense_id: int, e: schemas.ExpenseIn):
    if not repo.update_expense(expense_id, e.item, e.type, e.amount, e.week):
        raise HTTPException(404, "Expense not found")
    return {"ok": True}


@app.delete("/api/expenses/{expense_id}")
def remove_expense(expense_id: int):
    if not repo.delete_expense(expense_id):
        raise HTTPException(404, "Expense not found")
    return {"ok": True}


# --- Settings: categories ---

@app.get("/api/categories")
def get_categories():
    return repo.load_categories_full()


@app.post("/api/categories", status_code=201)
def create_category(c: schemas.CategoryIn):
    repo.add_category(c.type, c.bucket)
    return {"ok": True}


@app.put("/api/categories")
def update_category(c: schemas.CategoryIn):
    if c.old and c.old != c.type:
        repo.rename_category(c.old, c.type)
    repo.set_category_bucket(c.type, c.bucket)
    return {"ok": True}


@app.delete("/api/categories/{type_}")
def remove_category(type_: str):
    repo.delete_category(type_)
    return {"ok": True}


# --- Settings: budget ---

@app.get("/api/budget")
def get_budget():
    return repo.load_budget()


@app.put("/api/budget")
def upsert_budget(b: schemas.BudgetIn):
    if b.old and b.old != b.category:
        repo.rename_budget(b.old, b.category)
    repo.set_budget(b.category, b.amount)
    return {"ok": True}


@app.delete("/api/budget/{category}")
def remove_budget(category: str):
    repo.delete_budget(category)
    return {"ok": True}


# --- Settings: defaults ---

@app.get("/api/defaults")
def get_defaults():
    return repo.load_defaults()


@app.put("/api/defaults")
def upsert_default(d: schemas.DefaultIn):
    if d.old and d.old.strip().lower() != d.item.strip().lower():
        repo.delete_default(d.old)
    repo.set_default(d.item, d.type)
    return {"ok": True}


@app.delete("/api/defaults/{item}")
def remove_default(item: str):
    repo.delete_default(item)
    return {"ok": True}


# --- Settings: fixed monthly ---

@app.get("/api/fixed")
def get_fixed():
    return repo.load_fixed_rows()


@app.post("/api/fixed", status_code=201)
def create_fixed(f: schemas.FixedIn):
    return {"id": repo.add_fixed(f.item, f.type, f.cost)}


@app.put("/api/fixed/{fixed_id}")
def edit_fixed(fixed_id: int, f: schemas.FixedIn):
    if not repo.update_fixed(fixed_id, f.item, f.type, f.cost):
        raise HTTPException(404, "Fixed item not found")
    return {"ok": True}


@app.delete("/api/fixed/{fixed_id}")
def remove_fixed(fixed_id: int):
    if not repo.delete_fixed(fixed_id):
        raise HTTPException(404, "Fixed item not found")
    return {"ok": True}


# --- Settings: drag-and-drop reordering ---

@app.post("/api/categories/reorder")
def categories_reorder(order: list[str] = Body(..., embed=True)):
    repo.reorder_categories(order)
    return {"ok": True}


@app.post("/api/budget/reorder")
def budget_reorder(order: list[str] = Body(..., embed=True)):
    repo.reorder_budget(order)
    return {"ok": True}


@app.post("/api/defaults/reorder")
def defaults_reorder(order: list[str] = Body(..., embed=True)):
    repo.reorder_defaults(order)
    return {"ok": True}


@app.post("/api/fixed/reorder")
def fixed_reorder(order: list[int] = Body(..., embed=True)):
    repo.reorder_fixed(order)
    return {"ok": True}


# --- Serve the built frontend (when it exists) ---
# In production the Pi serves the React build from here; in dev Vite serves it.
_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(_DIST):
    app.mount("/", StaticFiles(directory=_DIST, html=True), name="static")
