"""Smoke test to confirm the app boots and the health endpoint responds."""
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


def make_client():
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({"DATABASE": db_path, "TESTING": True})
    return app.test_client()


def test_health():
    client = make_client()
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_register_and_login():
    client = make_client()
    r = client.post("/api/auth/register", json={"email": "a@b.com", "password": "pw123"})
    assert r.status_code == 201
    r = client.post("/api/auth/login", json={"email": "a@b.com", "password": "pw123"})
    assert r.status_code == 200
