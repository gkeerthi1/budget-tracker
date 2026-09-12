"""Computes budget rollover"""
from datetime import date

from aggregations import get_effective_budget, get_category_spent


def previous_month_str(month_str):
    year, month = (int(part) for part in month_str.split("-"))
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def apply_rollover_if_needed(conn, user_id, on_date=None):
    on_date = on_date or date.today()
    current_month = on_date.strftime("%Y-%m")
    prev_month = previous_month_str(current_month)

    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id = ?", (user_id,)
    ).fetchall()

    applied = []
    for cat in categories:
        already_done = conn.execute(
            "SELECT id FROM budget_rollovers WHERE user_id = ? AND category_id = ? AND month = ?",
            (user_id, cat["id"], current_month),
        ).fetchone()
        if already_done:
            continue

        prev_effective_budget = get_effective_budget(conn, user_id, cat, prev_month)
        prev_spent = get_category_spent(conn, user_id, cat["id"], prev_month)
        leftover = max(prev_effective_budget - prev_spent, 0)

        conn.execute(
            "INSERT INTO budget_rollovers (user_id, category_id, month, rollover_amount) "
            "VALUES (?, ?, ?, ?)",
            (user_id, cat["id"], current_month, leftover),
        )
        applied.append({"category_id": cat["id"], "month": current_month, "rollover_amount": leftover})

    conn.commit()
    return applied