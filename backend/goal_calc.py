"""Progress for savings goals: months remaining and the average
monthly contribution
"""
from datetime import date, datetime


def months_between(today, target_date):
    """Whole months from today to target_date"""
    months = (target_date.year - today.year) * 12 + (target_date.month - today.month)
    if target_date.day < today.day:
        months -= 1
    return max(months, 1)


def goal_progress(goal_row, today=None):
    today = today or date.today()
    target_date = datetime.strptime(goal_row["target_date"], "%Y-%m-%d").date()

    remaining = max(goal_row["target_amount"] - goal_row["current_amount"], 0)
    months_left = months_between(today, target_date)
    required_monthly = remaining / months_left if remaining > 0 else 0
    percent_complete = min(
        (goal_row["current_amount"] / goal_row["target_amount"]) * 100, 100
    )

    return {
        "remaining_amount": remaining,
        "months_left": months_left,
        "required_monthly_contribution": round(required_monthly, 2),
        "percent_complete": round(percent_complete, 2),
    }