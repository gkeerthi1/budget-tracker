"""Savings goal routes"""
from flask import Blueprint, request, jsonify, current_app

from models import get_db
from auth_utils import login_required, current_user_id
from validators import validate_positive_amount, validate_future_date
from goal_calc import goal_progress

goals_bp = Blueprint("goals", __name__, url_prefix="/api/goals")


def _goal_to_dict(row):
    data = {
        "id": row["id"],
        "name": row["name"],
        "target_amount": row["target_amount"],
        "target_date": row["target_date"],
        "current_amount": row["current_amount"],
    }
    data.update(goal_progress(row))
    return data


@goals_bp.route("", methods=["GET"])
@login_required
def list_goals():
    conn = get_db(current_app.config["DATABASE"])
    rows = conn.execute(
        "SELECT * FROM savings_goals WHERE user_id = ? ORDER BY target_date",
        (current_user_id(),),
    ).fetchall()
    conn.close()
    return jsonify([_goal_to_dict(r) for r in rows])


@goals_bp.route("", methods=["POST"])
@login_required
def create_goal():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    target_amount = data.get("target_amount")
    target_date = data.get("target_date")

    if not name:
        return jsonify({"error": "Goal name is required"}), 400

    valid, error = validate_positive_amount(target_amount)
    if not valid:
        return jsonify({"error": error}), 400

    valid, error = validate_future_date(target_date)
    if not valid:
        return jsonify({"error": error}), 400

    conn = get_db(current_app.config["DATABASE"])
    cur = conn.execute(
        "INSERT INTO savings_goals (user_id, name, target_amount, target_date, current_amount) "
        "VALUES (?, ?, ?, ?, 0)",
        (current_user_id(), name, target_amount, target_date),
    )
    conn.commit()
    new_row = conn.execute(
        "SELECT * FROM savings_goals WHERE id = ?", (cur.lastrowid,)
    ).fetchone()
    conn.close()
    return jsonify(_goal_to_dict(new_row)), 201


@goals_bp.route("/<int:goal_id>/contribute", methods=["POST"])
@login_required
def contribute(goal_id):
    data = request.get_json() or {}
    amount = data.get("amount")

    valid, error = validate_positive_amount(amount)
    if not valid:
        return jsonify({"error": error}), 400

    conn = get_db(current_app.config["DATABASE"])
    row = conn.execute(
        "SELECT * FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, current_user_id()),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Goal not found"}), 404

    conn.execute(
        "UPDATE savings_goals SET current_amount = current_amount + ? WHERE id = ?",
        (amount, goal_id),
    )
    conn.commit()
    updated = conn.execute(
        "SELECT * FROM savings_goals WHERE id = ?", (goal_id,)
    ).fetchone()
    conn.close()
    return jsonify(_goal_to_dict(updated))


@goals_bp.route("/<int:goal_id>", methods=["DELETE"])
@login_required
def delete_goal(goal_id):
    conn = get_db(current_app.config["DATABASE"])
    row = conn.execute(
        "SELECT * FROM savings_goals WHERE id = ? AND user_id = ?",
        (goal_id, current_user_id()),
    ).fetchone()
    if row is None:
        conn.close()
        return jsonify({"error": "Goal not found"}), 404

    conn.execute("DELETE FROM savings_goals WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Goal deleted"})