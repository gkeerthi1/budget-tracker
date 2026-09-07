import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
TODAY = date.today().isoformat()
from app import create_app


def make_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app.test_client()


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def make_category(client, name="Food", budget=300):
    return client.post("/api/categories", json={"name": name, "monthly_budget": budget}).get_json()


def test_transactions_require_login():
    client = make_client()
    resp = client.get("/api/transactions")
    assert resp.status_code == 401


def test_create_income_transaction():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/transactions", json={
        "type": "income", "amount": 2000, "spent_on": TODAY
    })
    assert resp.status_code == 201
    assert resp.get_json()["type"] == "income"


def test_create_expense_requires_category():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/transactions", json={
        "type": "expense", "amount": 50, "spent_on": TODAY
    })
    assert resp.status_code == 400


def test_create_expense_rejects_negative_amount():
    client = make_client()
    register_and_login(client)
    category = make_category(client)
    resp = client.post("/api/transactions", json={
        "type": "expense", "amount": -20, "category_id": category["id"], "spent_on": TODAY
    })
    assert resp.status_code == 400


def test_create_expense_rejects_future_date():
    client = make_client()
    register_and_login(client)
    category = make_category(client)
    resp = client.post("/api/transactions", json={
        "type": "expense", "amount": 20, "category_id": category["id"], "spent_on": "2099-01-01"
    })
    assert resp.status_code == 400


def test_expense_returns_remaining_balance():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=300)
    resp = client.post("/api/transactions", json={
        "type": "expense", "amount": 100, "category_id": category["id"], "spent_on": TODAY
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["remaining_balance"] == 200
    assert body["category_spent_this_month"] == 100


def test_list_transactions():
    client = make_client()
    register_and_login(client)
    category = make_category(client)
    client.post("/api/transactions", json={
        "type": "expense", "amount": 20, "category_id": category["id"], "spent_on": TODAY
    })
    client.post("/api/transactions", json={
        "type": "income", "amount": 500, "spent_on": "2026-08-02"
    })
    resp = client.get("/api/transactions")
    assert resp.status_code == 200
    assert len(resp.get_json()) == 2
