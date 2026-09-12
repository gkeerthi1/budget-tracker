"""Session-based authentication routes."""
from flask import Blueprint, request, jsonify, session, current_app
from werkzeug.security import generate_password_hash, check_password_hash

from models import get_db
from recurring_service import generate_due_transactions
from rollover_service import apply_rollover_if_needed

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db(current_app.config["DATABASE"])
    existing = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
    if existing:
        conn.close()
        return jsonify({"error": "An account with this email already exists"}), 409

    conn.execute(
        "INSERT INTO users (email, password_hash) VALUES (?, ?)",
        (email, generate_password_hash(password, method="pbkdf2:sha256")),
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Account created"}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    conn = get_db(current_app.config["DATABASE"])
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None or not check_password_hash(user["password_hash"], password):
        conn.close()
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = user["id"]
    apply_rollover_if_needed(conn, user["id"])
    generate_due_transactions(conn, user["id"])
    conn.close()
    return jsonify({"message": "Logged in", "email": user["email"]})


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})