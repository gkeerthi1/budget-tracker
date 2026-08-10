"""Tests for category management: CRUD, validation, and safe deletion."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


def make_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app.test_client()


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def test_categories_require_login():
    client = make_client()
    resp = client.get("/api/categories")
    assert resp.status_code == 401


def test_create_category():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/categories", json={"name": "Food", "monthly_budget": 300})
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Food"
    assert body["monthly_budget"] == 300


def test_create_category_requires_name():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/categories", json={"monthly_budget": 100})
    assert resp.status_code == 400


def test_create_category_rejects_negative_budget():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/categories", json={"name": "Rent", "monthly_budget": -50})
    assert resp.status_code == 400


def test_duplicate_category_name_rejected():
    client = make_client()
    register_and_login(client)
    client.post("/api/categories", json={"name": "Food", "monthly_budget": 100})
    resp = client.post("/api/categories", json={"name": "Food", "monthly_budget": 200})
    assert resp.status_code == 409


def test_list_categories():
    client = make_client()
    register_and_login(client)
    client.post("/api/categories", json={"name": "Food", "monthly_budget": 100})
    client.post("/api/categories", json={"name": "Rent", "monthly_budget": 900})
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    names = [c["name"] for c in resp.get_json()]
    assert set(names) == {"Food", "Rent"}


def test_update_category():
    client = make_client()
    register_and_login(client)
    created = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()
    resp = client.put(f"/api/categories/{created['id']}", json={"monthly_budget": 250})
    assert resp.status_code == 200
    assert resp.get_json()["monthly_budget"] == 250
    assert resp.get_json()["name"] == "Food"  # unchanged field preserved


def test_update_nonexistent_category_returns_404():
    client = make_client()
    register_and_login(client)
    resp = client.put("/api/categories/999", json={"monthly_budget": 50})
    assert resp.status_code == 404


def test_delete_category_unassigns_existing_transactions():
    """Deleting a category must not delete or break past transactions -
    it should unassign them instead (proposal requirement)."""
    client = make_client()
    register_and_login(client)
    category = client.post(
        "/api/categories", json={"name": "Food", "monthly_budget": 100}
    ).get_json()

    # Insert a transaction directly against this category via raw DB access,
    # since the transactions endpoint isn't built yet this week.
    import sqlite3
    from flask import current_app
    with client.application.app_context():
        db_path = current_app.config["DATABASE"]
    conn = sqlite3.connect(db_path)
    conn.execute(
        "INSERT INTO transactions (user_id, category_id, type, amount, spent_on) "
        "VALUES (1, ?, 'expense', 25.0, '2026-08-01')",
        (category["id"],),
    )
    conn.commit()
    conn.close()

    resp = client.delete(f"/api/categories/{category['id']}")
    assert resp.status_code == 200

    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT category_id FROM transactions").fetchone()
    conn.close()
    assert row[0] is None  # unassigned, not deleted
