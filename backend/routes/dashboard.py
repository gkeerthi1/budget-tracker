"""Dashboard summary routes"""
from flask import Blueprint, jsonify

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/api/dashboard")


@dashboard_bp.route("/summary", methods=["GET"])
def summary():
    return jsonify({"total_income": 0, "total_expenses": 0, "balance": 0})
