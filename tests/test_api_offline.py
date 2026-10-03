"""
Offline API tests: auth, validation, CORS, error handling, and agent fallback.

Dependencies are overridden with fakes, so these run without Supabase or Groq.
"""

import pytest
from fastapi.testclient import TestClient

from api.auth import CurrentUser, get_current_user, get_insights, get_repository
from backend.main import app
from backend.services.agent_service import AgentTools, ArwaAgent, _RateLimiter
from backend.services.errors import NotFoundError, RateLimitError
from backend.services.insights_service import InsightsService


class FakeRepo:
    """Just enough repository for routes that fail before touching data."""

    user_id = "user-1"

    def get_assignment(self, assignment_id):
        raise NotFoundError("Assignment not found")

    def get_profile(self):
        return {"id": self.user_id, "timezone": "America/New_York"}


class EmptyRepo(FakeRepo):
    """A brand-new student with no data at all."""

    def current_semester(self):
        return None

    def list_study_sessions(self, since=None):
        return []

    def list_assignments(self, course_id=None):
        return []

    def list_availability(self):
        return []

    def list_wellness(self, limit=30):
        return []


class ExplodingInsights:
    def dashboard(self):
        raise RuntimeError("database password is hunter2")


@pytest.fixture
def api():
    app.dependency_overrides[get_current_user] = lambda: CurrentUser("user-1", "a@b.co", "token")
    app.dependency_overrides[get_repository] = lambda: FakeRepo()
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def test_protected_routes_require_a_token():
    anon = TestClient(app)
    for path in ("/dashboard", "/plan", "/progress", "/courses", "/assignments", "/chat/messages", "/profile"):
        assert anon.get(path).status_code == 401, path
    assert anon.post("/chat", json={"message": "hi"}).status_code == 401


def test_body_validation(api):
    assert api.post("/assignments", json={}).status_code == 422
    assert api.post("/assignments", json={"title": "x", "course": "Bio", "due_date": "soon",
                                          "estimated_hours": 1}).status_code == 422
    assert api.post("/chat", json={"message": ""}).status_code == 422
    assert api.post("/chat", json={"message": "x" * 2001}).status_code == 422
    assert api.post("/wellness", json={"stress_level": 11}).status_code == 422
    assert api.put("/availability", json={"days": [{"weekday": 0, "minutes": 60},
                                                    {"weekday": 0, "minutes": 30}]}).status_code == 422
    assert api.put("/availability", json={"days": [{"weekday": 1, "minutes": 120,
                                                    "start_time": "23:30"}]}).status_code == 422
    assert api.patch("/profile", json={"timezone": "Mars/Olympus"}).status_code == 422


def test_frontend_cannot_choose_user_id(api):
    r = api.post("/assignments", json={"title": "x", "course": "Bio", "due_date": "2026-10-10",
                                       "estimated_hours": 1, "user_id": "someone-else"})
    assert r.status_code == 422


def test_domain_errors_map_to_status_codes(api):
    r = api.get("/assignments/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404 and r.json() == {"detail": "Assignment not found"}


def test_unexpected_errors_do_not_leak_details(api):
    app.dependency_overrides[get_insights] = lambda: ExplodingInsights()
    r = api.get("/dashboard")
    assert r.status_code == 500
    assert "hunter2" not in r.text and "Traceback" not in r.text


def test_cors_allows_only_configured_origins():
    client = TestClient(app)
    preflight = {"Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"}
    ok = client.options("/health", headers={"Origin": "http://localhost:3000", **preflight})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:3000"
    evil = client.options("/health", headers={"Origin": "https://evil.example", **preflight})
    assert "access-control-allow-origin" not in evil.headers


def test_health_never_exposes_secrets():
    body = TestClient(app).get("/health").text
    assert "gsk_" not in body and "eyJ" not in body


def test_rate_limiter_blocks_bursts():
    limiter = _RateLimiter(limit=2, window_seconds=60)
    limiter.check("u")
    limiter.check("u")
    with pytest.raises(RateLimitError):
        limiter.check("u")
    limiter.check("someone-else")


def test_agent_fallback_without_data_asks_for_courses(monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    reply = ArwaAgent(InsightsService(EmptyRepo())).reply("What should I do?", [])
    assert reply.ai_powered is False
    assert "course" in reply.content.lower()


def test_agent_tools_report_unknown_course_instead_of_guessing():
    tools = AgentTools(InsightsService(EmptyRepo()))
    result = tools.run("get_course_grade", {"course": "Marine Biology"})
    assert result["found"] is False and result["available_courses"] == []
    assert tools.run("get_courses", {})["note"]
    assert tools.run("not_a_tool", {}) == {"error": "Unknown tool not_a_tool"}
    assert tools.run("get_upcoming_assignments", {"days": "lots", "bogus": 1})["count"] == 0


def test_mark_complete_resolves_titles_and_refuses_unknown_or_ambiguous_ones():
    class Repo(EmptyRepo):
        completed: list = []

        def current_semester(self):
            return {"id": "s1"}

        def list_courses(self, semester_id=None):
            return [{"id": "c1", "name": "Organic Chemistry", "code": "CHEM 241"},
                    {"id": "c2", "name": "Linear Algebra", "code": "MATH 221"}]

        def list_assignments(self, course_id=None):
            row = {"category": "homework", "estimated_hours": 2, "completed": False, "due_date": "2026-10-09"}
            return [{**row, "id": "a1", "title": "Midterm 2", "course_id": "c1"},
                    {**row, "id": "a2", "title": "Problem Set 5", "course_id": "c2"},
                    {**row, "id": "a3", "title": "Reading", "course_id": "c1"},
                    {**row, "id": "a4", "title": "Reading", "course_id": "c2"}]

        def set_assignment_completed(self, assignment_id, completed):
            self.completed.append(assignment_id)
            return {"id": assignment_id, "title": "Problem Set 5"}

    repo = Repo()
    tools = AgentTools(InsightsService(repo))
    assert tools.run("mark_assignment_complete", {"title": "Problem Set 6"})["updated"] is False
    assert tools.run("mark_assignment_complete", {"title": "Reading"})["updated"] is False
    assert tools.run("mark_assignment_complete", {"assignment_id": "a1"})["updated"] is False
    assert repo.completed == []
    assert tools.run("mark_assignment_complete", {"title": " problem  set 5 "})["updated"] is True
    assert tools.run("mark_assignment_complete", {"title": "Reading", "course": "MATH 221"})["updated"] is True
    assert repo.completed == ["a2", "a4"]
