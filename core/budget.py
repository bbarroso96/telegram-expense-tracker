def compute_balance(budget: dict, expenses: list, type_bucket: dict) -> dict:
    """Returns {category: {budget, spent, remaining}} where spent is the sum of negative costs.

    `type_bucket` maps each expense type to its budget bucket (None = not budgeted).
    """
    spent = {cat: 0.0 for cat in budget}

    for _, _, type_, cost in expenses:
        if cost >= 0:
            continue
        cat = type_bucket.get(type_.strip())
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


def savings_target(not_budgeted: float, total_budget: float, total_spent: float,
                   is_current: bool = True) -> float:
    """Net income (not-budgeted: income + tax) minus a deduction.

    Ongoing month: deduct max(budget, spent) so the target is protected while
    within budget and erodes once you overspend. Ended month: deduct actual
    spend so unspent budget is banked as real savings. Shared by the web and bot.
    """
    deducted = max(total_budget, total_spent) if is_current else total_spent
    return not_budgeted - deducted
