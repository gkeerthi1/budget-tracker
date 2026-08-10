"""Shared auth helper for protecting routes that require a logged-in user."""
from functools import wraps
from flask import session, jsonify


def login_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"error": "Login required"}), 401
        return view_func(*args, **kwargs)
    return wrapped


def current_user_id():
    return session.get("user_id")