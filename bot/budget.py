def categorize_expense(type_: str) -> str | None:
    """Maps an expense type to a budget category.
    - Bill - * → 'Bill'
    - Groceries → 'Groceries'
    - Income, Tax → None (excluded from budget)
    - Everything else → 'The Rest'
    """
    t = type_.strip()
    if t.startswith("Bill"):
        return "Bill"
    if t == "Groceries":
        return "Groceries"
    if t in ("Income", "Tax"):
        return None
    return "The Rest"


def compute_balance(budget: dict, expenses: list) -> dict:
    """Returns {category: {budget, spent, remaining}} where spent is the sum of negative costs."""
    spent = {cat: 0.0 for cat in budget}

    for _, _, type_, cost in expenses:
        if cost >= 0:
            continue
        cat = categorize_expense(type_)
        if cat and cat in spent:
            spent[cat] += abs(cost)

    return {
        cat: {
            "budget":    budget_amt,
            "spent":     spent.get(cat, 0.0),
            "remaining": budget_amt - spent.get(cat, 0.0),
        }
        for cat, budget_amt in budget.items()
    }
