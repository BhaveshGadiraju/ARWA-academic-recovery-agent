"""
AI grounding tests: real Groq + real Supabase data.

These check that ARWA's answers come from tool results: it names real
assignments, quotes the calculated Recovery Score, admits missing data, and
only changes data when the student clearly asks.
"""

import os
import re

import pytest

from tests.conftest import auth_headers

pytestmark = [pytest.mark.live, pytest.mark.ai]


@pytest.fixture(scope="module", autouse=True)
def needs_groq():
    if not os.environ.get("GROQ_API_KEY"):
        pytest.skip("GROQ_API_KEY not configured")


def ask(client, token: str, message: str) -> dict:
    r = client.post("/chat", json={"message": message}, headers=auth_headers(token))
    assert r.status_code == 201, r.text
    return r.json()


def test_recommendation_names_real_assignments(client, live_tokens, seeded):
    reply = ask(client, live_tokens["a"], "What should I work on tonight?")
    text = reply["message"]["content"]
    assert reply["ai_powered"] is True
    assert reply["tools_used"]
    real_titles = ["Midterm 2", "Lab Report 4", "Problem Set 6", "Reading Response"]
    assert any(t.lower() in text.lower() for t in real_titles), text


def test_quotes_calculated_score(client, live_tokens, seeded):
    score = client.get("/dashboard", headers=auth_headers(live_tokens["a"])).json()["score"]["score"]
    reply = ask(client, live_tokens["a"], "Why is my Recovery Score what it is?")
    text = reply["message"]["content"]
    assert "Recovery Score" in reply["tools_used"]
    assert re.search(rf"\b{score}\b", text), f"expected score {score} in: {text}"


def test_admits_unknown_course(client, live_tokens, seeded):
    reply = ask(client, live_tokens["a"], "What's my grade in Marine Biology?")
    text = reply["message"]["content"].lower()
    assert not re.search(r"marine biology[^.]*\b\d{2,3}(\.\d)?%", text), text
    assert any(w in text for w in ("don't", "do not", "no ", "not ", "isn't", "only")), text


def test_reports_missing_data_for_empty_account(client, live_tokens, seeded):
    reply = ask(client, live_tokens["b"], "What's due this week and what should I study?")
    text = reply["message"]["content"].lower()
    for invented in ("midterm 2", "lab report 4", "problem set 6"):
        assert invented not in text
    assert any(w in text for w in ("add", "no courses", "don't have", "haven't", "no assignments")), text


def test_marks_complete_only_when_told(client, live_tokens, seeded):
    h = auth_headers(live_tokens["a"])
    pset = seeded["assignments"]["pset"]
    others = [a for key, a in seeded["assignments"].items() if key != "pset" and not a["completed"]]
    ask(client, live_tokens["a"], "I just finished Problem Set 6 for Linear Algebra, please mark it done.")
    assert client.get(f"/assignments/{pset['id']}", headers=h).json()["completed"] is True
    for other in others:
        assert client.get(f"/assignments/{other['id']}", headers=h).json()["completed"] is False, other["title"]

    history = client.get("/chat/messages", headers=h).json()
    assert history[-1]["role"] == "assistant"
    assert history[-1]["metadata"]["tools_used"]
