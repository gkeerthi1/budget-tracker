"""Category management routes: create, list, edit, delete."""
from flask import Blueprint, request, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from validators import validate_non_negative_amount
from aggregations import get_remaining_balance, budget_status, get_effective_budget, get_rollover_amount

categories_bp = Blueprint("categories", __name__, url_prefix="/api/categories")


def _category_to_dict(conn, user_id, row, with_status=True):
    data = {
        "id": row["id"],
        "name": row["name"],
        "monthly_budget": row["monthly_budget"],
    }
    if with_status:
        remaining, spent = get_remaining_balance(conn, user_id, row)
        effective_budget = get_effective_budget(conn, user_id, row)
        data["rollover_amount"] = get_rollover_amount(conn, user_id, row["id"])
        data["effective_budget"] = effective_budget
        data["spent_this_month"] = spent
        data["remaining_balance"] = remaining
        data["status"] = budget_status(spent, effective_budget)
    return data


@categories_bp.route("", methods=["GET"])
@login_required
def list_categories():
    conn = get_db(current_app.config["DATABASE"])
    rows = conn.execute(
        "SELECT * FROM categories WHERE user_id = ? ORDER BY name",
        (current_user_id(),),
    ).fetchall()
    result = [_category_to_dict(conn, current_user_id(), r) for r in rows]
    conn.close()
    return jsonify(result)


@categories_bp.route("", methods=["POST"])
@login_required
def create_category():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    monthly_budget = data.get("monthly_budget", 0)

    if not name:
        return jsonify({"error": "Category name is required"}), 400

    valid, error = validate_non_negative_amount(monthly_budget)
    if not valid:
        return jsonify({"error": error}), 400

    conn = get_db(current_app.config["DATABASE"])
    existing = conn.execute(
        "SELECT id FROM categories WHERE user_id = ? AND name = ?",
        (current_user_id(), name),
    ).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "A category with this name already exists"}), 409

    cur = conn.execute(
        "INSERT INTO categories (user_id, name, monthly_budget) VALUES (?, ?, ?)",
        (current_user_id(), name, monthly_budget or 0),
    )
    conn.commit()
    new_row = conn.execute("SELECT * FROM categories WHERE id = ?", (cur.lastrowid,)).fetchone()
    result = _category_to_dict(conn, current_user_id(), new_row)
    conn.close()
    return jsonify(result), 201


@categories_bp.route("/<int:category_id>", methods=["PUT"])
@login_required
def update_category(category_id):
    data = request.get_json() or {}
    conn = get_db(current_app.config["DATABASE"])
    row = conn.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?",
        (category_id, current_user_id()),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Category not found"}), 404

    name = data.get("name", row["name"]).strip()
    monthly_budget = data.get("monthly_budget", row["monthly_budget"])

    if not name:
        conn.close()
        return jsonify({"error": "Category name is required"}), 400

    valid, error = validate_non_negative_amount(monthly_budget)
    if not valid:
        conn.close()
        return jsonify({"error": error}), 400

    conn.execute(
        "UPDATE categories SET name = ?, monthly_budget = ? WHERE id = ?",
        (name, monthly_budget, category_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM categories WHERE id = ?", (category_id,)).fetchone()
    result = _category_to_dict(conn, current_user_id(), updated)
    conn.close()
    return jsonify(result)


@categories_bp.route("/<int:category_id>", methods=["DELETE"])
@login_required
def delete_category(category_id):
    conn = get_db(current_app.config["DATABASE"])
    row = conn.execute(
        "SELECT * FROM categories WHERE id = ? AND user_id = ?",
        (category_id, current_user_id()),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Category not found"}), 404

    conn.execute(
        "UPDATE transactions SET category_id = NULL WHERE category_id = ?",
        (category_id,),
    )
    conn.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Category deleted"})