"""Tests for recurring transactions: rule CRUD and monthly generation.

Generation is tested by calling recurring_service.generate_due_transactions
directly with an explicit on_date, rather than relying on real time to
pass - this lets us simulate month rollovers deterministically.
"""
import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import get_db
from recurring_service import generate_due_transactions


def make_app_and_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app, app.test_client(), db_path


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def test_recurring_requires_login():
    app, client, _ = make_app_and_client()
    resp = client.get("/api/recurring")
    assert resp.status_code == 401


def test_create_recurring_rule():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    resp = client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 1, "note": "Salary"
    })
    assert resp.status_code == 201
    assert resp.get_json()["day_of_month"] == 1


def test_create_expense_rule_requires_category():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    resp = client.post("/api/recurring", json={
        "type": "expense", "amount": 1200, "day_of_month": 1
    })
    assert resp.status_code == 400


def test_create_rule_rejects_invalid_day():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    resp = client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 31
    })
    assert resp.status_code == 400


def test_list_and_delete_rule():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    created = client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 1
    }).get_json()

    resp = client.get("/api/recurring")
    assert len(resp.get_json()) == 1

    resp = client.delete(f"/api/recurring/{created['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/recurring")
    assert len(resp.get_json()) == 0


def test_generate_skips_when_not_due_yet():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 20, "note": "Salary"
    })

    conn = get_db(db_path)
    generated = generate_due_transactions(conn, 1, on_date=date(2026, 9, 5))
    conn.close()
    assert generated == []


def test_generate_creates_transaction_when_due():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 5, "note": "Salary"
    })

    conn = get_db(db_path)
    generated = generate_due_transactions(conn, 1, on_date=date(2026, 9, 10))
    conn.close()
    assert len(generated) == 1


def test_generate_does_not_duplicate_same_month():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 5, "note": "Salary"
    })

    conn = get_db(db_path)
    first = generate_due_transactions(conn, 1, on_date=date(2026, 9, 10))
    second = generate_due_transactions(conn, 1, on_date=date(2026, 9, 25))
    conn.close()
    assert len(first) == 1
    assert len(second) == 0


def test_generate_creates_again_next_month():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 5, "note": "Salary"
    })

    conn = get_db(db_path)
    september = generate_due_transactions(conn, 1, on_date=date(2026, 9, 10))
    october = generate_due_transactions(conn, 1, on_date=date(2026, 10, 6))
    conn.close()
    assert len(september) == 1
    assert len(october) == 1


def test_login_triggers_generation_for_due_rule():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/recurring", json={
        "type": "income", "amount": 3000, "day_of_month": 1, "note": "Salary"
    })

    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "user@test.com", "password": "pw12345"})

    resp = client.get("/api/transactions")
    transactions = resp.get_json()
    assert any("Recurring" in (t["note"] or "") for t in transactions)