"""Logic for generating recurring transactions (rent, salary, etc.) on
their configured day of month.
"""
import calendar
from datetime import date


def _clamp_day(year, month, day):
    """Handles rules set for day 29-31 landing safely in shorter months"""
    last_day = calendar.monthrange(year, month)[1]
    return min(day, last_day)


def generate_due_transactions(conn, user_id, on_date=None):
    on_date = on_date or date.today()
    month_str = on_date.strftime("%Y-%m")

    rules = conn.execute(
        "SELECT * FROM recurring_transactions WHERE user_id = ? AND is_active = 1",
        (user_id,),
    ).fetchall()

    generated_ids = []
    for rule in rules:
        if rule["last_generated_month"] == month_str:
            continue  # already generated for this month
        if rule["day_of_month"] > on_date.day:
            continue  # not due yet this month

        spent_on_day = _clamp_day(on_date.year, on_date.month, rule["day_of_month"])
        spent_on = date(on_date.year, on_date.month, spent_on_day).isoformat()
        note = f"Recurring: {rule['note']}" if rule["note"] else "Recurring transaction"

        cur = conn.execute(
            "INSERT INTO transactions (user_id, category_id, type, amount, spent_on, note) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, rule["category_id"], rule["type"], rule["amount"], spent_on, note),
        )
        conn.execute(
            "UPDATE recurring_transactions SET last_generated_month = ? WHERE id = ?",
            (month_str, rule["id"]),
        )
        generated_ids.append(cur.lastrowid)

    conn.commit()
    return generated_ids