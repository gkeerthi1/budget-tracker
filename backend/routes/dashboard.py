"""Dashboard summary"""
from flask import Blueprint, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from aggregations import get_month_totals, get_remaining_balance, budget_status, get_effective_budget

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


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