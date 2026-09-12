"""Tests for month-to-month dashboard comparison."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import get_db
from aggregations import current_month
from routes.dashboard import _shift_month, _last_n_months


def make_app_and_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app, app.test_client(), db_path


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def insert_expense(db_path, user_id, category_id, amount, month_str, day="15"):
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO transactions (user_id, category_id, type, amount, spent_on, note) "
        "VALUES (?, ?, 'expense', ?, ?, '')",
        (user_id, category_id, amount, f"{month_str}-{day}"),
    )
    conn.commit()
    conn.close()


def insert_income(db_path, user_id, amount, month_str, day="01"):
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO transactions (user_id, category_id, type, amount, spent_on, note) "
        "VALUES (?, NULL, 'income', ?, ?, '')",
        (user_id, amount, f"{month_str}-{day}"),
    )
    conn.commit()
    conn.close()


# ---------- Month arithmetic helpers ----------

def test_shift_month_forward_within_year():
    assert _shift_month("2026-03", 2) == "2026-05"


def test_shift_month_backward_across_year_boundary():
    assert _shift_month("2026-01", -1) == "2025-12"


def test_last_n_months_ends_at_given_month_oldest_first():
    result = _last_n_months(3, end_month="2026-09")
    assert result == ["2026-07", "2026-08", "2026-09"]


def test_last_n_months_defaults_to_real_current_month():
    result = _last_n_months(1)
    assert result == [current_month()]


# ---------- API tests ----------

def test_compare_requires_login():
    app, client, _ = make_app_and_client()
    resp = client.get("/api/dashboard/compare")
    assert resp.status_code == 401


def test_compare_default_range_is_six_months_ending_now():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    resp = client.get("/api/dashboard/compare")
    body = resp.get_json()
    assert len(body["months"]) == 6
    assert body["months"][-1]["month"] == current_month()


def test_compare_months_param_is_clamped():
    app, client, _ = make_app_and_client()
    register_and_login(client)
    resp = client.get("/api/dashboard/compare?months=99")
    assert len(resp.get_json()["months"]) == 12

    resp = client.get("/api/dashboard/compare?months=0")
    assert len(resp.get_json()["months"]) == 1


def test_compare_shows_correct_totals_per_month():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 200}).get_json()

    this_month = current_month()
    last_month = _shift_month(this_month, -1)

    insert_expense(db_path, 1, category["id"], 50, last_month)
    insert_income(db_path, 1, 1000, last_month)
    insert_expense(db_path, 1, category["id"], 80, this_month)
    insert_income(db_path, 1, 1200, this_month)

    resp = client.get("/api/dashboard/compare?months=2")
    months = {m["month"]: m for m in resp.get_json()["months"]}

    assert months[last_month]["total_expenses"] == 50
    assert months[last_month]["total_income"] == 1000
    assert months[this_month]["total_expenses"] == 80
    assert months[this_month]["total_income"] == 1200


def test_compare_reflects_per_month_category_status():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    this_month = current_month()
    last_month = _shift_month(this_month, -1)

    insert_expense(db_path, 1, category["id"], 30, last_month)   # 30% - no warning
    insert_expense(db_path, 1, category["id"], 95, this_month)   # 95% - approaching

    resp = client.get("/api/dashboard/compare?months=2")
    months = {m["month"]: m for m in resp.get_json()["months"]}

    assert months[last_month]["categories"][0]["status"] is None
    assert months[this_month]["categories"][0]["status"] == "approaching_limit"


def test_compare_shows_zero_for_months_before_category_existed():
    """A category created this month should show 0 spent for earlier
    months in the comparison window, not an error"""
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "New Category", "monthly_budget": 50}).get_json()

    resp = client.get("/api/dashboard/compare?months=3")
    months = resp.get_json()["months"]
    for month_entry in months[:-1]:  # all but the current month
        assert month_entry["categories"][0]["spent_this_month"] == 0