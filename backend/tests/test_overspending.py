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


def make_category(client, name="Food", budget=100):
    return client.post("/api/categories", json={"name": name, "monthly_budget": budget}).get_json()


def spend(client, category_id, amount, day="2026-08-01"):
    return client.post("/api/transactions", json={
        "type": "expense", "amount": amount, "category_id": category_id, "spent_on": day
    })


def test_no_warning_below_80_percent():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    resp = spend(client, category["id"], 70)
    assert resp.get_json()["budget_warning"] is None


def test_warning_at_80_percent():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    resp = spend(client, category["id"], 80)
    assert resp.get_json()["budget_warning"] == "approaching_limit"


def test_warning_at_81_percent():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    resp = spend(client, category["id"], 81)
    assert resp.get_json()["budget_warning"] == "approaching_limit"


def test_over_budget_at_100_percent():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    resp = spend(client, category["id"], 100)
    assert resp.get_json()["budget_warning"] == "over_budget"


def test_over_budget_above_100_percent():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    resp = spend(client, category["id"], 150)
    assert resp.get_json()["budget_warning"] == "over_budget"


def test_overall_warning_across_categories():
    client = make_client()
    register_and_login(client)
    food = make_category(client, name="Food", budget=100)
    rent = make_category(client, name="Rent", budget=100)
    # Total budget across categories = 200. Spend 210 total -> over_budget overall.
    spend(client, food["id"], 100)
    resp = spend(client, rent["id"], 110)
    assert resp.get_json()["overall_warning"] == "over_budget"


def test_category_status_reflected_in_list_endpoint():
    client = make_client()
    register_and_login(client)
    category = make_category(client, budget=100)
    spend(client, category["id"], 90)
    resp = client.get("/api/categories")
    body = resp.get_json()
    assert body[0]["status"] == "approaching_limit"
    assert body[0]["remaining_balance"] == 10
