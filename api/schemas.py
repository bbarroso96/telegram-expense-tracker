from pydantic import BaseModel


class ExpenseIn(BaseModel):
    item: str
    type: str
    amount: float
    week: int


class CategoryIn(BaseModel):
    type: str
    bucket: str | None = None
    old: str | None = None  # previous name, when renaming


class BudgetIn(BaseModel):
    category: str
    amount: float
    old: str | None = None  # previous name, when renaming


class DefaultIn(BaseModel):
    item: str
    type: str
    old: str | None = None  # previous merchant key, when renaming


class FixedIn(BaseModel):
    item: str
    type: str
    cost: float
