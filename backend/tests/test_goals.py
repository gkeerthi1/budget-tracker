"""Tests for savings goals"""
import os
import sys
import tempfile
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from goal_calc import goal_progress, months_between

FUTURE_DATE = (date.today() + timedelta(days=200)).isoformat()
PAST_DATE = (date.today() - timedelta(days=10)).isoformat()


def make_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app.test_client()


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def test_goals_require_login():
    client = make_client()
    resp = client.get("/api/goals")
    assert resp.status_code == 401


def test_create_goal():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/goals", json={
        "name": "Emergency Fund", "target_amount": 5000, "target_date": FUTURE_DATE
    })
    assert resp.status_code == 201
    body = resp.get_json()
    assert body["name"] == "Emergency Fund"
    assert body["current_amount"] == 0
    assert body["remaining_amount"] == 5000
    assert body["percent_complete"] == 0


def test_create_goal_rejects_past_date():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/goals", json={
        "name": "Vacation", "target_amount": 2000, "target_date": PAST_DATE
    })
    assert resp.status_code == 400


def test_create_goal_rejects_negative_amount():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/goals", json={
        "name": "Vacation", "target_amount": -100, "target_date": FUTURE_DATE
    })
    assert resp.status_code == 400


def test_contribute_updates_progress():
    client = make_client()
    register_and_login(client)
    goal = client.post("/api/goals", json={
        "name": "Emergency Fund", "target_amount": 1000, "target_date": FUTURE_DATE
    }).get_json()

    resp = client.post(f"/api/goals/{goal['id']}/contribute", json={"amount": 250})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["current_amount"] == 250
    assert body["remaining_amount"] == 750
    assert body["percent_complete"] == 25.0


def test_contribute_rejects_negative_amount():
    client = make_client()
    register_and_login(client)
    goal = client.post("/api/goals", json={
        "name": "Emergency Fund", "target_amount": 1000, "target_date": FUTURE_DATE
    }).get_json()

    resp = client.post(f"/api/goals/{goal['id']}/contribute", json={"amount": -50})
    assert resp.status_code == 400


def test_contribute_to_nonexistent_goal_returns_404():
    client = make_client()
    register_and_login(client)
    resp = client.post("/api/goals/999/contribute", json={"amount": 50})
    assert resp.status_code == 404


def test_delete_goal():
    client = make_client()
    register_and_login(client)
    goal = client.post("/api/goals", json={
        "name": "Emergency Fund", "target_amount": 1000, "target_date": FUTURE_DATE
    }).get_json()

    resp = client.delete(f"/api/goals/{goal['id']}")
    assert resp.status_code == 200

    resp = client.get("/api/goals")
    assert resp.get_json() == []


def test_percent_complete_caps_at_100():
    client = make_client()
    register_and_login(client)
    goal = client.post("/api/goals", json={
        "name": "Small Goal", "target_amount": 100, "target_date": FUTURE_DATE
    }).get_json()

    client.post(f"/api/goals/{goal['id']}/contribute", json={"amount": 150})
    resp = client.get("/api/goals")
    assert resp.get_json()[0]["percent_complete"] == 100


def test_months_between_calculation():
    assert months_between(date(2026, 9, 6), date(2027, 3, 6)) == 6


def test_months_between_minimum_one():
    assert months_between(date(2026, 9, 20), date(2026, 9, 5)) == 1


def test_required_monthly_contribution_math():
    row = {
        "target_amount": 1200,
        "current_amount": 0,
        "target_date": "2027-03-06",
    }
    result = goal_progress(row, today=date(2026, 9, 6))
    assert result["months_left"] == 6
    assert result["required_monthly_contribution"] == 200.0