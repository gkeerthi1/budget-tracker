"""Transaction routes: record income/expense, list transactions."""
from flask import Blueprint, request, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from validators import validate_positive_amount, validate_not_future_date
from aggregations import get_remaining_balance, budget_status, get_overall_status, get_effective_budget

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


def _transaction_to_dict(row):
    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "type": row["type"],
        "amount": row["amount"],
        "spent_on": row["spent_on"],
        "note": row["note"],
    }


@transactions_bp.route("", methods=["GET"])
@login_required
def list_transactions():
    conn = get_db(current_app.config["DATABASE"])
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY spent_on DESC, id DESC",
        (current_user_id(),),
    ).fetchall()
    conn.close()
    return jsonify([_transaction_to_dict(r) for r in rows])


@transactions_bp.route("", methods=["POST"])
@login_required
def create_transaction():
    data = request.get_json() or {}
    tx_type = data.get("type")
    amount = data.get("amount")
    spent_on = data.get("spent_on")
    category_id = data.get("category_id")
    note = data.get("note", "")

    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Type must be 'income' or 'expense'"}), 400

    valid, error = validate_positive_amount(amount)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = validate_not_future_date(spent_on)
    if not valid:
        return jsonify({"error": error}), 400

    if tx_type == "expense" and not category_id:
        return jsonify({"error": "category_id is required for expenses"}), 400

    conn = get_db(current_app.config["DATABASE"])

    category = None
    if category_id:
        category = conn.execute(
            "SELECT * FROM categories WHERE id = ? AND user_id = ?",
            (category_id, current_user_id()),
        ).fetchone()
        if category is None:
            conn.close()
            return jsonify({"error": "Category not found"}), 404

    cur = conn.execute(
        "INSERT INTO transactions (user_id, category_id, type, amount, spent_on, note) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (current_user_id(), category_id, tx_type, amount, spent_on, note),
    )
    conn.commit()

    response = {
        "id": cur.lastrowid,
        "category_id": category_id,
        "type": tx_type,
        "amount": amount,
        "spent_on": spent_on,
        "note": note,
    }

    if tx_type == "expense" and category is not None:
        remaining, spent = get_remaining_balance(conn, current_user_id(), category)
        effective_budget = get_effective_budget(conn, current_user_id(), category)
        response["remaining_balance"] = remaining
        response["category_spent_this_month"] = spent
        response["budget_warning"] = budget_status(spent, effective_budget)

        total_budget, total_expenses, overall_flag = get_overall_status(conn, current_user_id())
        response["overall_warning"] = overall_flag

    conn.close()
    return jsonify(response), 201