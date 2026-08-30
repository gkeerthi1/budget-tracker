"""Tests for the dashboard summary"""
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


def test_dashboard_requires_login():
    client = make_client()
    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 401


def test_dashboard_totals():
    client = make_client()
    register_and_login(client)
    category = client.post(
        "/api/categories", json={"name": "Food", "monthly_budget": 300}
    ).get_json()

    client.post("/api/transactions", json={
        "type": "income", "amount": 2000, "spent_on": "2026-08-01"
    })
    client.post("/api/transactions", json={
        "type": "expense", "amount": 100, "category_id": category["id"], "spent_on": "2026-08-02"
    })

    resp = client.get("/api/dashboard/summary")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["total_income"] == 2000
    assert body["total_expenses"] == 100
    assert body["balance"] == 1900
    assert len(body["categories"]) == 1
    assert body["categories"][0]["remaining_balance"] == 200


def test_dashboard_with_no_data():
    client = make_client()
    register_and_login(client)
    resp = client.get("/api/dashboard/summary")
    body = resp.get_json()
    assert body["total_income"] == 0
    assert body["total_expenses"] == 0
    assert body["categories"] == []