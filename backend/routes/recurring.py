"""Recurring transaction rules: e.g. rent or salary that repeats on a
set day every month."""
from flask import Blueprint, request, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from validators import validate_positive_amount
from recurring_service import generate_due_transactions

recurring_bp = Blueprint("recurring", __name__, url_prefix="/api/recurring")


def _rule_to_dict(row):
    return {
        "id": row["id"],
        "category_id": row["category_id"],
        "type": row["type"],
        "amount": row["amount"],
        "day_of_month": row["day_of_month"],
        "note": row["note"],
        "is_active": bool(row["is_active"]),
    }


@recurring_bp.route("", methods=["GET"])
@login_required
def list_rules():
    conn = get_db(current_app.config["DATABASE"])
    rows = conn.execute(
        "SELECT * FROM recurring_transactions WHERE user_id = ? ORDER BY day_of_month",
        (current_user_id(),),
    ).fetchall()
    conn.close()
    return jsonify([_rule_to_dict(r) for r in rows])


@recurring_bp.route("", methods=["POST"])
@login_required
def create_rule():
    data = request.get_json() or {}
    tx_type = data.get("type")
    amount = data.get("amount")
    day_of_month = data.get("day_of_month")
    category_id = data.get("category_id")
    note = data.get("note", "")

    if tx_type not in ("income", "expense"):
        return jsonify({"error": "Type must be 'income' or 'expense'"}), 400

    valid, error = validate_positive_amount(amount)
    if not valid:
        return jsonify({"error": error}), 400

    if not isinstance(day_of_month, int) or not (1 <= day_of_month <= 28):
        return jsonify({"error": "day_of_month must be an integer between 1 and 28"}), 400

    if tx_type == "expense" and not category_id:
        return jsonify({"error": "category_id is required for expense rules"}), 400

    conn = get_db(current_app.config["DATABASE"])

    if category_id:
        category = conn.execute(
            "SELECT id FROM categories WHERE id = ? AND user_id = ?",
            (category_id, current_user_id()),
        ).fetchone()
        if category is None:
            conn.close()
            return jsonify({"error": "Category not found"}), 404

    cur = conn.execute(
        "INSERT INTO recurring_transactions "
        "(user_id, category_id, type, amount, day_of_month, note, is_active) "
        "VALUES (?, ?, ?, ?, ?, ?, 1)",
        (current_user_id(), category_id, tx_type, amount, day_of_month, note),
    )
    conn.commit()
    new_row = conn.execute(
        "SELECT * FROM recurring_transactions WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return jsonify(_rule_to_dict(new_row)), 201


@recurring_bp.route("/<int:rule_id>", methods=["DELETE"])
@login_required
def delete_rule(rule_id):
    conn = get_db(current_app.config["DATABASE"])
    row = conn.execute(
        "SELECT * FROM recurring_transactions WHERE id = ? AND user_id = ?",
        (rule_id, current_user_id()),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Recurring rule not found"}), 404

    conn.execute("DELETE FROM recurring_transactions WHERE id = ?", (rule_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Recurring rule deleted"})


@recurring_bp.route("/generate", methods=["POST"])
@login_required
def generate_now():
    """Manually trigger generation of due recurring transactions.
    Runs automatically on login too; exposed here for testing/demo."""
    conn = get_db(current_app.config["DATABASE"])
    generated_ids = generate_due_transactions(conn, current_user_id())
    conn.close()
    return jsonify({"generated_transaction_ids": generated_ids})