"""
Live end-to-end API tests against the real Supabase project.

They exercise the core loop (profile → semester → courses → assignments →
study time → dashboard → plan → complete work) and prove that one user can
never read or change another user's data. Skipped unless .env.test exists.
"""

from datetime import timedelta
from typing import List

import pytest

from tests.conftest import auth_headers as _headers
from tests.conftest import local_today as _today

pytestmark = pytest.mark.live


def _ids(items: List[dict], key: str = "assignment_id") -> set:
    return {i[key] for i in items if i.get(key)}


class TestCoreLoop:
    def test_dashboard_is_grounded_in_real_data(self, client, live_tokens, seeded):
        r = client.get("/dashboard", headers=_headers(live_tokens["a"]))
        assert r.status_code == 200, r.text
        d = r.json()
        real_ids = {a["id"] for a in seeded["assignments"].values()}

        assert isinstance(d["score"]["score"], int) and 0 <= d["score"]["score"] <= 100
        assert d["score"]["factors"], "score must explain itself"
        assert {m["key"] for m in d["metrics"]} == {"workload", "deadline_pressure", "performance", "capacity"}
        assert _ids(d["priorities"]) <= real_ids
        kinds = {r["kind"] for r in d["risks"]}
        assert "overdue" in kinds and "upcoming_exam" in kinds
        assert d["today"]["overdue_count"] == 1
        assert len(d["courses"]) == 2
        chem = next(c for c in d["courses"] if c["code"] == "CHEM 241")
        assert chem["grade"] == 65.0

    def test_plan_only_schedules_real_assignments(self, client, live_tokens, seeded):
        r = client.get("/plan?days=7", headers=_headers(live_tokens["a"]))
        assert r.status_code == 200, r.text
        plan = r.json()
        blocks = [b for day in plan["days"] for b in day["blocks"] if b["kind"] == "study"]
        assert blocks
        assert _ids(blocks) <= {a["id"] for a in seeded["assignments"].values() if not a["completed"]}
        for day in plan["days"]:
            assert day["study_minutes"] <= day["window_minutes"]

    def test_course_detail(self, client, live_tokens, seeded):
        course = seeded["courses"]["CHEM 241"]
        r = client.get(f"/courses/{course['id']}", headers=_headers(live_tokens["a"]))
        assert r.status_code == 200, r.text
        detail = r.json()
        assert detail["course"]["name"] == "Organic Chemistry"
        assert {a["title"] for a in detail["assignments"]} == {"Midterm 2", "Lab Report 4", "Quiz 3"}
        assert detail["recommended_action"]

    def test_completing_work_updates_progress(self, client, live_tokens, seeded):
        h = _headers(live_tokens["a"])
        before = client.get("/dashboard", headers=h).json()["today"]["tasks_remaining"]
        lab = seeded["assignments"]["lab"]
        r = client.put(f"/assignments/{lab['id']}", json={"completed": True}, headers=h)
        assert r.status_code == 200 and r.json()["completed"] is True
        assert r.json()["completed_at"]
        after = client.get("/dashboard", headers=h).json()["today"]["tasks_remaining"]
        assert after == before - 1

        r = client.get("/progress", headers=h)
        assert r.status_code == 200, r.text
        assert r.json()["totals"]["completed"] >= 2

    def test_past_work_entered_as_completed_is_not_marked_late(self, client, live_tokens, seeded):
        graded = seeded["assignments"]["graded"]
        assert graded["completed"] is True and graded["completed_at"] is None
        r = client.get("/progress", headers=_headers(live_tokens["a"]))
        assert graded["id"] not in {m["assignment_id"] for m in r.json()["missed"]}

    def test_study_session_and_wellness(self, client, live_tokens, seeded):
        h = _headers(live_tokens["a"])
        exam = seeded["assignments"]["exam"]
        r = client.post("/study-sessions", json={"assignment_id": exam["id"], "minutes": 50}, headers=h)
        assert r.status_code == 201, r.text
        future = (_today() + timedelta(days=3)).isoformat()
        r = client.post("/study-sessions", json={"assignment_id": exam["id"], "minutes": 50, "session_date": future},
                        headers=h)
        assert r.status_code == 422
        r = client.post("/wellness", json={"stress_level": 6, "sleep_hours": 7}, headers=h)
        assert r.status_code == 201, r.text


class TestValidationAndErrors:
    def test_requires_auth(self, client):
        assert client.get("/dashboard").status_code == 401
        assert client.get("/assignments", headers=_headers("not-a-token")).status_code == 401

    def test_rejects_invalid_bodies(self, client, live_tokens, seeded):
        h = _headers(live_tokens["a"])
        course_id = seeded["courses"]["MATH 221"]["id"]
        bad = [
            {"title": "", "course_id": course_id, "due_date": "2026-10-10", "estimated_hours": 1},
            {"title": "X", "course_id": course_id, "due_date": "2026-10-10", "estimated_hours": -1},
            {"title": "X", "course_id": course_id, "due_date": "2026-10-10", "estimated_hours": 1, "category": "party"},
            {"title": "X", "course_id": course_id, "due_date": "2026-10-10", "estimated_hours": 1, "points_earned": 5},
            {"title": "X", "course_id": course_id, "due_date": "2026-10-10", "estimated_hours": 1, "user_id": "x"},
        ]
        for body in bad:
            r = client.post("/assignments", json=body, headers=h)
            assert r.status_code == 422, (body, r.text)
            assert "Traceback" not in r.text

    def test_unknown_ids_are_404(self, client, live_tokens, seeded):
        h = _headers(live_tokens["a"])
        missing = "00000000-0000-0000-0000-000000000000"
        assert client.get(f"/assignments/{missing}", headers=h).status_code == 404
        assert client.get(f"/courses/{missing}", headers=h).status_code == 404
        assert client.get("/assignments/not-a-uuid", headers=h).status_code == 422


class TestIsolation:
    """User B must never see or modify user A's data."""

    def test_lists_are_scoped(self, client, live_tokens, seeded):
        hb = _headers(live_tokens["b"])
        assert client.get("/assignments", headers=hb).json() == []
        assert client.get("/courses", headers=hb).json() == []
        assert client.get("/semesters", headers=hb).json() == []

    def test_cannot_read_or_modify_other_users_rows(self, client, live_tokens, seeded):
        hb = _headers(live_tokens["b"])
        exam = seeded["assignments"]["exam"]
        course = seeded["courses"]["CHEM 241"]
        assert client.get(f"/assignments/{exam['id']}", headers=hb).status_code == 404
        assert client.put(f"/assignments/{exam['id']}", json={"completed": True}, headers=hb).status_code == 404
        assert client.delete(f"/assignments/{exam['id']}", headers=hb).status_code == 404
        assert client.get(f"/courses/{course['id']}", headers=hb).status_code == 404
        assert client.delete(f"/courses/{course['id']}", headers=hb).status_code == 404
        r = client.post("/study-sessions", json={"assignment_id": exam["id"], "minutes": 30}, headers=hb)
        assert r.status_code == 404

        still_there = client.get(f"/assignments/{exam['id']}", headers=_headers(live_tokens["a"]))
        assert still_there.status_code == 200 and still_there.json()["completed"] is False

    def test_cannot_attach_rows_to_other_users_parents(self, client, live_tokens, seeded):
        hb = _headers(live_tokens["b"])
        r = client.post("/courses", json={"name": "Sneaky", "semester_id": seeded["semester"]["id"]}, headers=hb)
        assert r.status_code in (404, 422), r.text
        r = client.post("/assignments", json={"title": "Sneaky", "course_id": seeded["courses"]["CHEM 241"]["id"],
                                              "due_date": "2026-10-10", "estimated_hours": 1}, headers=hb)
        assert r.status_code in (404, 422), r.text
