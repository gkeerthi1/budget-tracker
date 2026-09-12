"""Tests for budget rollover."""
import os
import sys
import tempfile
from datetime import date

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import get_db
from rollover_service import apply_rollover_if_needed, previous_month_str
from aggregations import get_effective_budget


def make_app_and_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app, app.test_client(), db_path


def register_and_login(client, email="user@test.com", password="pw12345"):
    client.post("/api/auth/register", json={"email": email, "password": password})
    client.post("/api/auth/login", json={"email": email, "password": password})


def spend(client, category_id, amount, day):
    return client.post("/api/transactions", json={
        "type": "expense", "amount": amount, "category_id": category_id, "spent_on": day
    })


def insert_past_expense(db_path, user_id, category_id, amount, spent_on):
    """Insert a transaction directly into the DB, bypassing the API's
    not-future-date validation. Needed when a test simulates a month
    that may have already become 'the future' relative to whenever
    these tests actually run - the same stale-date trap that hit the
    Week 2 tests, avoided here by never routing simulated-month data
    through real-clock-dependent validation."""
    conn = get_db(db_path)
    conn.execute(
        "INSERT INTO transactions (user_id, category_id, type, amount, spent_on, note) "
        "VALUES (?, ?, 'expense', ?, ?, '')",
        (user_id, category_id, amount, spent_on),
    )
    conn.commit()
    conn.close()


# ---------- Unit tests: rollover calculation ----------

def test_previous_month_str_normal_case():
    assert previous_month_str("2026-09") == "2026-08"


def test_previous_month_str_year_boundary():
    assert previous_month_str("2026-01") == "2025-12"


def test_full_budget_rolls_over_when_nothing_spent():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    conn = get_db(db_path)
    applied = apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    conn.close()
    # Nothing spent in August -> the entire 100 base budget rolls over.
    assert applied[0]["rollover_amount"] == 100


def test_rollover_carries_unspent_amount():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    # Spend only 60 of 100 in August.
    spend(client, category["id"], 60, "2026-08-15")

    conn = get_db(db_path)
    applied = apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    conn.close()
    assert applied[0]["rollover_amount"] == 40


def test_rollover_is_zero_when_over_budget():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    spend(client, category["id"], 150, "2026-08-15")  # overspent August

    conn = get_db(db_path)
    applied = apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    conn.close()
    assert applied[0]["rollover_amount"] == 0  # never negative


def test_rollover_not_recomputed_on_second_call_same_month():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    client.post("/api/categories", json={"name": "Food", "monthly_budget": 100})

    conn = get_db(db_path)
    first = apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    second = apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 15))
    conn.close()
    assert len(first) == 1
    assert len(second) == 0  # already computed for September


def test_rollover_compounds_across_multiple_months():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    insert_past_expense(db_path, 1, category["id"], 60, "2026-08-15")  # August: 40 leftover

    conn = get_db(db_path)
    apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))  # Sept effective budget = 140
    conn.close()

    insert_past_expense(db_path, 1, category["id"], 100, "2026-09-15")  # Sept: 40 leftover of 140

    conn = get_db(db_path)
    applied = apply_rollover_if_needed(conn, 1, on_date=date(2026, 10, 1))
    conn.close()
    assert applied[0]["rollover_amount"] == 40


# ---------- Integration: rollover + overspending interaction ----------

def test_rollover_raises_the_overspending_threshold():
    """An expense that would trip 'over_budget' against the base budget
    should NOT trip it once rollover has increased the effective budget -
    this is the exact interaction the proposal identified as risky."""
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()

    spend(client, category["id"], 50, "2026-08-15")  # August: 50 leftover

    conn = get_db(db_path)
    apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))  # Sept effective budget = 150
    conn.close()

    # 120 against a BASE budget of 100 would be over_budget (120%).
    # Against the EFFECTIVE budget of 150, it's only 80% - approaching, not over.
    resp = spend(client, category["id"], 120, "2026-09-10")
    assert resp.get_json()["budget_warning"] == "approaching_limit"


def test_dashboard_reflects_effective_budget_after_rollover():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()
    spend(client, category["id"], 50, "2026-08-15")

    conn = get_db(db_path)
    apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    conn.close()

    resp = client.get("/api/dashboard/summary")
    cat_summary = resp.get_json()["categories"][0]
    assert cat_summary["effective_budget"] == 150


def test_category_list_exposes_rollover_amount():
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()
    spend(client, category["id"], 30, "2026-08-15")

    conn = get_db(db_path)
    apply_rollover_if_needed(conn, 1, on_date=date(2026, 9, 1))
    conn.close()

    resp = client.get("/api/categories")
    body = resp.get_json()[0]
    assert body["rollover_amount"] == 70
    assert body["effective_budget"] == 170


# ---------- Integration: rollover + recurring transactions on login ----------

def test_login_applies_rollover_and_recurring_together():
    """Both rollover and recurring-transaction generation are triggered
    on login. This confirms they don't interfere with each other when
    run back to back in the same request."""
    app, client, db_path = make_app_and_client()
    register_and_login(client)
    category = client.post("/api/categories", json={"name": "Food", "monthly_budget": 100}).get_json()
    spend(client, category["id"], 40, "2026-08-15")  # August: 60 leftover

    client.post("/api/recurring", json={
        "type": "income", "amount": 500, "day_of_month": 1, "note": "Salary"
    })

    # Fresh login triggers both rollover (for September) and the recurring rule.
    client.post("/api/auth/logout")
    client.post("/api/auth/login", json={"email": "user@test.com", "password": "pw12345"})

    categories = client.get("/api/categories").get_json()
    transactions = client.get("/api/transactions").get_json()

    assert categories[0]["rollover_amount"] == 60
    assert any("Recurring" in (t["note"] or "") for t in transactions)