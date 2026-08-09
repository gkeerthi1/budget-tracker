"""Transaction routes"""
from flask import Blueprint, jsonify

transactions_bp = Blueprint("transactions", __name__, url_prefix="/api/transactions")


@transactions_bp.route("", methods=["GET"])
def list_transactions():
    return jsonify([])
