"""Shared pytest setup: import path, env loading, and live-test fixtures."""

import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict

import pytest
from dotenv import dotenv_values

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
TEST_TIMEZONE = "America/New_York"

for env_file in (".env", ".env.test"):
    for key, value in dotenv_values(PROJECT_ROOT / env_file).items():
        if value is not None:
            os.environ.setdefault(key, value)

LIVE_ENV = ("SUPABASE_URL", "SUPABASE_ANON_KEY", "ARWA_TEST_PASSWORD", "ARWA_TEST_EMAIL_A", "ARWA_TEST_EMAIL_B")


def _sign_in(email: str) -> str:
    from supabase import create_client

    client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_ANON_KEY"])
    session = client.auth.sign_in_with_password({"email": email, "password": os.environ["ARWA_TEST_PASSWORD"]})
    return session.session.access_token


@pytest.fixture(scope="session")
def live_tokens() -> Dict[str, str]:
    """Access tokens for two confirmed QA users (skips when not configured)."""
    missing = [k for k in LIVE_ENV if not os.environ.get(k)]
    if missing:
        pytest.skip(f"Live tests need {', '.join(missing)} (see README: Testing)")
    return {"a": _sign_in(os.environ["ARWA_TEST_EMAIL_A"]), "b": _sign_in(os.environ["ARWA_TEST_EMAIL_B"])}


@pytest.fixture(scope="session")
def client():
    """In-process FastAPI client."""
    from fastapi.testclient import TestClient

    from backend.main import app

    return TestClient(app)


def auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def local_today() -> date:
    return datetime.now(ZoneInfo(TEST_TIMEZONE)).date()


def _reset(client, token: str) -> None:
    """Remove the user's academic data so every run starts clean."""
    h = auth_headers(token)
    for a in client.get("/assignments", headers=h).json():
        client.delete(f"/assignments/{a['id']}", headers=h)
    for s in client.get("/semesters", headers=h).json():
        client.delete(f"/semesters/{s['id']}", headers=h)
    client.put("/availability", json={"days": []}, headers=h)
    client.delete("/chat/messages", headers=h)


@pytest.fixture(scope="module")
def seeded(client, live_tokens):
    """User A with a realistic semester; user B with an empty account."""
    h = auth_headers(live_tokens["a"])
    _reset(client, live_tokens["a"])
    _reset(client, live_tokens["b"])
    today = local_today()

    r = client.patch("/profile", json={"full_name": "QA Alpha", "timezone": TEST_TIMEZONE}, headers=h)
    assert r.status_code == 200, r.text
    r = client.post("/semesters", json={"name": "Fall 2026"}, headers=h)
    assert r.status_code == 201, r.text
    semester = r.json()

    courses = {}
    for name, code in (("Organic Chemistry", "CHEM 241"), ("Linear Algebra", "MATH 221")):
        r = client.post("/courses", json={"name": name, "code": code, "target_grade": 85}, headers=h)
        assert r.status_code == 201, r.text
        courses[code] = r.json()

    def add(title: str, code: str, days: int, hours: float, **extra) -> dict:
        body = {"title": title, "course_id": courses[code]["id"], "due_date": (today + timedelta(days=days)).isoformat(),
                "estimated_hours": hours, **extra}
        r = client.post("/assignments", json=body, headers=h)
        assert r.status_code == 201, r.text
        return r.json()

    assignments = {
        "exam": add("Midterm 2", "CHEM 241", 2, 6, category="exam"),
        "lab": add("Lab Report 4", "CHEM 241", 1, 2, category="lab"),
        "pset": add("Problem Set 6", "MATH 221", 4, 3),
        "overdue": add("Reading Response", "MATH 221", -2, 1, category="reading"),
        "graded": add("Quiz 3", "CHEM 241", -7, 1, category="quiz", completed=True,
                      points_possible=20, points_earned=13),
    }
    days = [{"weekday": d, "minutes": 120, "start_time": "18:00"} for d in range(7)]
    r = client.put("/availability", json={"days": days}, headers=h)
    assert r.status_code == 200, r.text
    return {"semester": semester, "courses": courses, "assignments": assignments}
