from datetime import date


def current_month():
    return date.today().strftime("%Y-%m")


def _month_like(month_str):
    return f"{month_str}%"


def get_category_spent(conn, user_id, category_id, month=None):
    month = month or current_month()
    row = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
        "WHERE user_id = ? AND category_id = ? AND type = 'expense' AND spent_on LIKE ?",
        (user_id, category_id, _month_like(month)),
    ).fetchone()
    return row["total"]


def get_remaining_balance(conn, user_id, category_row, month=None):
    spent = get_category_spent(conn, user_id, category_row["id"], month)
    return category_row["monthly_budget"] - spent, spent


def get_month_totals(conn, user_id, month=None):
    month = month or current_month()
    income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
        "WHERE user_id = ? AND type = 'income' AND spent_on LIKE ?",
        (user_id, _month_like(month)),
    ).fetchone()["total"]
    expenses = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM transactions "
        "WHERE user_id = ? AND type = 'expense' AND spent_on LIKE ?",
        (user_id, _month_like(month)),
    ).fetchone()["total"]
    return income, expenses


def budget_status(spent, budget):
    if not budget or budget <= 0:
        return None
    percent = (spent / budget) * 100
    if percent >= 100:
        return "over_budget"
    if percent >= 80:
        return "approaching_limit"
    return None


def get_overall_status(conn, user_id, month=None):
    month = month or current_month()
    total_budget = conn.execute(
        "SELECT COALESCE(SUM(monthly_budget), 0) AS total FROM categories WHERE user_id = ?",
        (user_id,),
    ).fetchone()["total"]
    _, total_expenses = get_month_totals(conn, user_id, month)
    return total_budget, total_expenses, budget_status(total_expenses, total_budget)
