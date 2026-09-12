"""Dashboard summary"""
from flask import Blueprint, request, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from aggregations import (
    get_month_totals, get_remaining_balance, budget_status,
    get_effective_budget, current_month,
)

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


def _shift_month(month_str, delta):
    """Shift a 'YYYY-MM' string by delta months (negative = earlier)."""
    year, month = map(int, month_str.split("-"))
    total = year * 12 + (month - 1) + delta
    new_year = total // 12
    new_month = total % 12 + 1
    return f"{new_year}-{new_month:02d}"


def _last_n_months(n, end_month=None):
    """Returns n month strings ending at end_month (default: current
    month), oldest first - convenient order for charting a trend."""
    end_month = end_month or current_month()
    return [_shift_month(end_month, -i) for i in range(n - 1, -1, -1)]


@dashboard_bp.route("/summary", methods=["GET"])
@login_required
def summary():
    conn = get_db(current_app.config["DATABASE"])
    user_id = current_user_id()

    total_income, total_expenses = get_month_totals(conn, user_id)

    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()

    category_summaries = []
    for cat in categories:
        remaining, spent = get_remaining_balance(conn, user_id, cat)
        effective_budget = get_effective_budget(conn, user_id, cat)
        category_summaries.append({
            "id": cat["id"],
            "name": cat["name"],
            "monthly_budget": cat["monthly_budget"],
            "effective_budget": effective_budget,
            "spent_this_month": spent,
            "remaining_balance": remaining,
            "status": budget_status(spent, effective_budget),
        })

    conn.close()
    return jsonify({
        "total_income": total_income,
        "total_expenses": total_expenses,
        "balance": total_income - total_expenses,
        "categories": category_summaries,
    })


@dashboard_bp.route("/compare", methods=["GET"])
@login_required
def compare():
    """Month-to-month comparison across recent months (default 6,
    clamped 1-12 via ?months=). Uses currently-existing categories -
    a category always shows 0 spent for months before it existed,
    since a transaction can't reference a category that doesn't exist
    yet, so this stays accurate without needing per-month category
    snapshots."""
    n = request.args.get("months", default=6, type=int)
    n = max(1, min(n, 12))

    conn = get_db(current_app.config["DATABASE"])
    user_id = current_user_id()

    months = _last_n_months(n)
    categories = conn.execute(
        "SELECT * FROM categories WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()

    monthly_results = []
    for month in months:
        total_income, total_expenses = get_month_totals(conn, user_id, month)
        category_summaries = []
        for cat in categories:
            remaining, spent = get_remaining_balance(conn, user_id, cat, month)
            effective_budget = get_effective_budget(conn, user_id, cat, month)
            category_summaries.append({
                "id": cat["id"],
                "name": cat["name"],
                "effective_budget": effective_budget,
                "spent_this_month": spent,
                "remaining_balance": remaining,
                "status": budget_status(spent, effective_budget),
            })
        monthly_results.append({
            "month": month,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "balance": total_income - total_expenses,
            "categories": category_summaries,
        })

    conn.close()
    return jsonify({"months": monthly_results})