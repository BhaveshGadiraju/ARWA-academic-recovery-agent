"""
ARWA AI agent (Groq tool calling).

The model answers questions by calling backend tools that return the
student's stored data ("student_data") or ARWA's deterministic calculations
("arwa_calculation"). It never receives a raw database dump and is told to
quote calculated values instead of computing its own. When Groq is not
configured or fails, a deterministic fallback answers from the same engine.
"""

import inspect
import json
import logging
import os
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Callable, Deque, Dict, List, Optional

from backend.services import academic_engine as engine
from backend.services.domain import DayAvailability
from backend.services.errors import NotFoundError, RateLimitError
from backend.services.insights_service import Analysis, InsightsService

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "openai/gpt-oss-120b"
MAX_TOOL_ROUNDS = 5
HISTORY_MESSAGES = 12
RATE_LIMIT_MESSAGES = 20
RATE_LIMIT_WINDOW_SECONDS = 600

TOOL_LABELS = {
    "get_student_profile": "Profile",
    "get_courses": "Courses",
    "get_upcoming_assignments": "Upcoming assignments",
    "get_overdue_assignments": "Overdue assignments",
    "get_course_grade": "Course grade",
    "calculate_recovery_score": "Recovery Score",
    "analyze_academic_risk": "Risk analysis",
    "get_available_study_time": "Study time",
    "generate_recovery_plan": "Recovery plan",
    "mark_assignment_complete": "Marked complete",
}

SYSTEM_PROMPT = """You are ARWA, an Academic Recovery & Wellness Agent helping one college student.
Today is {today_long}. The student's local time is {local_time} ({timezone}).

You can only know the student's situation through your tools. Tool results are labelled:
- source "student_data": facts the student entered (courses, assignments, grades, deadlines, study time).
- source "arwa_calculation": values ARWA's backend calculated (Recovery Score, metrics, risks, priorities, plan).

Rules:
1. Call tools before answering anything about the student's courses, work, grades, time, score, or plan.
2. Never invent or guess assignments, courses, grades, deadlines, study hours, or history. Whenever you mention an assignment, write its full exact title from the tool result, never a paraphrase. Never give made-up example assignment or course names.
3. Quote calculated numbers exactly. Never compute your own Recovery Score, grade, or metric.
4. Keep three kinds of statements distinct: what the student's data shows, what ARWA calculated, and your own recommendation (say "I'd suggest" / "I recommend").
5. If something needed is missing (no courses, no study time, no grades, no such course), say exactly what is missing and where to add it in ARWA.
6. If the work does not fit the available time, say so plainly and help triage. Never pretend everything fits.
   For "what should I work on" or scheduling questions, call generate_recovery_plan and follow its blocks, order, and times. Never propose study times outside the student's study windows.
7. The Recovery Score is an ARWA planning metric, not a scientific or clinical measure.
8. Only call mark_assignment_complete when the student clearly says they finished a specific assignment, passing that assignment's exact title. If it reports no match or several matches, ask the student; never mark a different assignment. When it succeeds, confirm that in your first sentence.
9. No medical advice. If the student mentions serious distress, be kind and suggest reaching out to someone they trust or campus support.
10. Be warm, direct, and brief: usually under 140 words. Formatting: short paragraphs, "- " bullet lists, and **bold** only (no headings, tables, or links). Show times like "6:00 PM"."""


def _tool(name: str, description: str, properties: Optional[Dict[str, Any]] = None, required: Optional[List[str]] = None):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {"type": "object", "properties": properties or {}, "required": required or []},
        },
    }


TOOLS = [
    _tool("get_student_profile", "The student's profile, today's date, and what data they have entered."),
    _tool("get_courses", "Current-semester courses with grade, course health, pending work, and next deadline."),
    _tool(
        "get_upcoming_assignments",
        "Incomplete assignments due in the next N days, with remaining estimated minutes.",
        {
            "days": {"type": "integer", "description": "How many days ahead (1-30). Default 7."},
            "course": {"type": "string", "description": "Optional course name or code to filter by."},
        },
    ),
    _tool("get_overdue_assignments", "Incomplete assignments whose due date has passed."),
    _tool(
        "get_course_grade",
        "Current grade for one course, calculated from recorded points.",
        {"course": {"type": "string", "description": "Course name or code."}},
        ["course"],
    ),
    _tool("calculate_recovery_score", "ARWA's Recovery Score with the factor breakdown and formula."),
    _tool("analyze_academic_risk", "Deterministic academic risks with severity, reason, data, and recommended action."),
    _tool(
        "get_available_study_time",
        "The student's study windows for the next N days compared with the work due.",
        {"days": {"type": "integer", "description": "How many days (1-14). Default 7."}},
    ),
    _tool(
        "generate_recovery_plan",
        "ARWA's schedule of real assignments in the student's real study windows, plus work that doesn't fit.",
        {"days": {"type": "integer", "description": "How many days to plan (1-7). Default 3."}},
    ),
    _tool(
        "mark_assignment_complete",
        "Mark one of the student's incomplete assignments complete, identified by its exact title.",
        {
            "title": {"type": "string", "description": "The assignment's full exact title, as the student named it."},
            "course": {"type": "string", "description": "Optional course name or code, if two assignments share a title."},
        },
        ["title"],
    ),
]


@dataclass
class AgentReply:
    """The agent's answer plus how it was produced."""

    content: str
    tools_used: List[str] = field(default_factory=list)
    ai_powered: bool = True


class _RateLimiter:
    """Simple in-memory sliding window per user (protects the Groq key from abuse)."""

    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > self.window:
                hits.popleft()
            if len(hits) >= self.limit:
                raise RateLimitError("You're sending messages quickly. Give ARWA a minute and try again.")
            hits.append(now)


chat_rate_limiter = _RateLimiter(RATE_LIMIT_MESSAGES, RATE_LIMIT_WINDOW_SECONDS)


_UNICODE_REPLACEMENTS = str.maketrans({
    "\u00a0": " ", "\u202f": " ", "\u2009": " ", "\u2007": " ",
    "\u2011": "-", "\u2010": "-",
})


def _normalize_text(text: str) -> str:
    """Replace the non-breaking spaces/hyphens models like to emit with plain ASCII ones."""
    return text.translate(_UNICODE_REPLACEMENTS).strip()


def _title_key(title: str) -> str:
    """Case- and whitespace-insensitive form of an assignment title, for exact matching."""
    return " ".join(_normalize_text(title).casefold().split())


def _clamp_int(value: Any, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(high, int(value)))
    except (TypeError, ValueError):
        return default


def _window_label(day: date, window: DayAvailability) -> str:
    """A study window as people say it, e.g. '6:00 PM - 8:00 PM'."""
    start = datetime.combine(day, window.start_time)
    end = start + timedelta(minutes=window.minutes)
    return f"{engine.format_clock(start.strftime('%H:%M'))} - {engine.format_clock(end.strftime('%H:%M'))}"


class AgentTools:
    """Backend functions the model can call. Results are compact and labelled by source."""

    def __init__(self, insights: InsightsService):
        self.insights = insights
        self._analysis: Optional[Analysis] = None

    @property
    def analysis(self) -> Analysis:
        if self._analysis is None:
            self._analysis = self.insights.analyze(plan_days=7)
        return self._analysis

    def run(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        handler: Optional[Callable[..., Dict[str, Any]]] = getattr(self, f"tool_{name}", None)
        if handler is None:
            return {"error": f"Unknown tool {name}"}
        accepted = inspect.signature(handler).parameters
        kwargs = {k: v for k, v in arguments.items() if k in accepted}
        try:
            return handler(**kwargs)
        except NotFoundError as exc:
            return {"error": exc.message}

    def _matches_course(self, assignment, query: str) -> bool:
        """True if the assignment's course name or code contains the query."""
        needle = query.strip().lower()
        course = self.analysis.snapshot.course(assignment.course_id)
        names = [assignment.course_name, course.code if course else None]
        return any(needle in name.lower() for name in names if name)

    def _assignment_view(self, a) -> Dict[str, Any]:
        today = self.analysis.snapshot.today
        return {
            "title": a.title,
            "course": a.course_name,
            "category": a.category,
            "due_date": a.due_date.isoformat(),
            "due": engine.describe_due(a.due_date, today),
            "remaining_minutes": a.remaining_minutes,
        }

    def tool_get_student_profile(self) -> Dict[str, Any]:
        snap, profile = self.analysis.snapshot, self.analysis.profile
        wellness = snap.wellness
        return {
            "source": "student_data",
            "name": profile.get("full_name"),
            "school": profile.get("school"),
            "major": profile.get("major"),
            "year_in_school": profile.get("year_in_school"),
            "today": snap.today.isoformat(),
            "course_count": len(snap.courses),
            "assignment_count": len(snap.assignments),
            "has_study_time": any(d.minutes > 0 for d in snap.availability.values()),
            "has_grades": any(a.is_graded for a in snap.assignments),
            "latest_stress_level": wellness.stress_level if wellness else None,
        }

    def tool_get_courses(self) -> Dict[str, Any]:
        snap = self.analysis.snapshot
        courses = []
        for course in snap.courses:
            health = engine.course_health(course, snap)
            courses.append({
                "course_id": course.id,
                "name": course.name,
                "code": course.code,
                "grade_percent": health.grade,
                "target_grade": health.target_grade,
                "course_health": health.health,
                "status": health.status,
                "summary": health.summary,
                "pending_assignments": health.pending_count,
                "next_due": health.next_due.model_dump(mode="json") if health.next_due else None,
            })
        return {"source": "student_data + arwa_calculation", "courses": courses,
                "note": None if courses else "The student has not added any courses."}

    def tool_get_upcoming_assignments(self, days: Any = 7, course: Optional[str] = None) -> Dict[str, Any]:
        snap = self.analysis.snapshot
        horizon = snap.today + timedelta(days=_clamp_int(days, 7, 1, 30))
        items = [a for a in engine.incomplete(snap.assignments) if snap.today <= a.due_date <= horizon]
        if course:
            items = [a for a in items if self._matches_course(a, course)]
        items.sort(key=lambda a: a.due_date)
        return {"source": "student_data", "assignments": [self._assignment_view(a) for a in items],
                "count": len(items)}

    def tool_get_overdue_assignments(self) -> Dict[str, Any]:
        items = engine.overdue(self.analysis.snapshot)
        return {"source": "student_data", "assignments": [self._assignment_view(a) for a in items], "count": len(items)}

    def tool_get_course_grade(self, course: str = "") -> Dict[str, Any]:
        snap = self.analysis.snapshot
        needle = (course or "").strip().lower()
        match = next((c for c in snap.courses if needle and (needle in c.name.lower() or needle == (c.code or "").lower()
                                                             or needle in (c.code or "").lower())), None)
        if match is None:
            return {"source": "student_data", "found": False,
                    "available_courses": [c.code or c.name for c in snap.courses]}
        graded = [a for a in snap.assignments if a.course_id == match.id and a.is_graded]
        return {
            "source": "arwa_calculation",
            "found": True,
            "course": match.name,
            "grade_percent": engine.course_grade(match.id, snap.assignments),
            "target_grade": match.target_grade,
            "graded_items": [{"title": a.title, "earned": a.points_earned, "possible": a.points_possible} for a in graded],
            "method": "Total points earned / total points possible across graded assignments.",
        }

    def tool_calculate_recovery_score(self) -> Dict[str, Any]:
        score = self.analysis.score
        return {
            "source": "arwa_calculation",
            "score": score.score,
            "band": score.band_label,
            "headline": score.headline,
            "factors": [f.model_dump() for f in score.factors],
            "metrics": [{"metric": m.label, "value": m.value, "level": m.level, "summary": m.summary}
                        for m in self.analysis.metrics],
            "formula": (
                "Weighted average of Performance 30%, Completion 20%, Capacity 30%, Deadline headroom 20% "
                "(components without data are skipped and weights re-normalised), minus 5 points per overdue item (max 15)."
            ),
            "disclaimer": "ARWA planning metric, not a scientifically validated measure.",
        }

    def tool_analyze_academic_risk(self) -> Dict[str, Any]:
        risks = self.analysis.risks
        return {"source": "arwa_calculation", "risks": [r.model_dump(mode="json") for r in risks[:8]],
                "count": len(risks)}

    def tool_get_available_study_time(self, days: Any = 7) -> Dict[str, Any]:
        n = _clamp_int(days, 7, 1, 14)
        snap = self.analysis.snapshot
        schedule = []
        for offset in range(n):
            day = snap.today + timedelta(days=offset)
            window = snap.availability.get(day.weekday())
            has_window = bool(window and window.minutes)
            minutes = (engine.window_minutes_left_today(snap.now, window) if offset == 0
                       else (window.minutes if has_window else 0))
            entry: Dict[str, Any] = {
                "date": day.isoformat(),
                "weekday": day.strftime("%A"),
                "minutes_available": minutes,
                "study_window": _window_label(day, window) if has_window else None,
            }
            if offset == 0 and has_window and minutes == 0:
                entry["note"] = "Today's study window has already passed."
            schedule.append(entry)
        return {
            "source": "student_data + arwa_calculation",
            "days": schedule,
            "total_available_minutes": engine.available_minutes(snap, n),
            "work_due_in_period_minutes": engine.required_minutes(snap, n),
            "note": None if any(d.minutes > 0 for d in snap.availability.values())
            else "The student has not set any weekly study time.",
        }

    def tool_generate_recovery_plan(self, days: Any = 3) -> Dict[str, Any]:
        n = _clamp_int(days, 3, 1, 7)
        plan = self.analysis.plan
        return {
            "source": "arwa_calculation",
            "days": [
                {
                    "date": d.date.isoformat(),
                    "label": d.label,
                    "study_minutes": d.study_minutes,
                    "blocks": [b.model_dump(mode="json", exclude_none=True) for b in d.blocks],
                }
                for d in plan.days[:n]
            ],
            "work_that_does_not_fit": [u.model_dump(mode="json") for u in plan.unscheduled],
            "is_feasible": plan.is_feasible,
            "top_priorities": [
                {"rank": p.rank, "title": p.title, "course": p.course_name, "reason": p.reason,
                 "remaining_minutes": p.remaining_minutes}
                for p in self.analysis.priorities[:5]
            ],
        }

    def tool_mark_assignment_complete(self, title: Any = "", course: Any = None) -> Dict[str, Any]:
        """Resolve the title server-side so a mis-copied id can never complete the wrong assignment."""
        wanted = _title_key(str(title or ""))
        if not wanted:
            return {"updated": False, "error": "title is required"}
        pending = engine.incomplete(self.analysis.snapshot.assignments)
        matches = [a for a in pending if _title_key(a.title) == wanted]
        if course and len(matches) > 1:
            matches = [a for a in matches if self._matches_course(a, str(course))]
        if len(matches) != 1:
            return {
                "updated": False,
                "error": "No incomplete assignment has that exact title." if not matches
                else "More than one incomplete assignment has that title. Ask the student which course.",
                "incomplete_assignments": [{"title": a.title, "course": a.course_name} for a in (matches or pending)],
            }
        row = self.insights.repo.set_assignment_completed(matches[0].id, True)
        self._analysis = None
        return {"source": "student_data", "updated": True, "title": row["title"], "course": matches[0].course_name}


class ArwaAgent:
    """Runs one chat turn: tools + Groq, or the deterministic fallback."""

    def __init__(self, insights: InsightsService):
        self.insights = insights
        self.tools = AgentTools(insights)

    def reply(self, message: str, history: List[Dict[str, str]]) -> AgentReply:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            try:
                return self._groq_reply(api_key, message, history)
            except Exception:
                logger.exception("Groq agent failed; using deterministic fallback")
        return self._fallback_reply(message)

    # ── Groq ─────────────────────────────────────────────────────────────────

    def _system_prompt(self) -> str:
        profile = self.insights.repo.get_profile()
        now = self.insights.local_now(profile)
        return SYSTEM_PROMPT.format(
            today_long=now.strftime("%A, %B %d, %Y"),
            local_time=now.strftime("%I:%M %p").lstrip("0"),
            timezone=profile.get("timezone") or "UTC",
        )

    def _groq_reply(self, api_key: str, message: str, history: List[Dict[str, str]]) -> AgentReply:
        import groq

        # Retries honour Groq's retry-after header, which matters on the free tier's tokens-per-minute cap.
        client = groq.Groq(api_key=api_key, timeout=45.0, max_retries=3)
        model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
        messages: List[Dict[str, Any]] = [{"role": "system", "content": self._system_prompt()}]
        messages += [{"role": m["role"], "content": m["content"]} for m in history[-HISTORY_MESSAGES:]]
        messages.append({"role": "user", "content": message})
        tools_used: List[str] = []

        for round_index in range(MAX_TOOL_ROUNDS + 1):
            last_round = round_index == MAX_TOOL_ROUNDS
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="none" if last_round else ("required" if round_index == 0 else "auto"),
                temperature=0.2,
                max_completion_tokens=1500,
            )
            choice = response.choices[0].message
            calls = choice.tool_calls or []
            if not calls:
                content = _normalize_text(choice.content or "")
                if not content:
                    raise RuntimeError("Empty response from model")
                return AgentReply(content=content, tools_used=tools_used, ai_powered=True)

            messages.append({
                "role": "assistant",
                "content": choice.content or "",
                "tool_calls": [
                    {"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                    for c in calls
                ],
            })
            for call in calls:
                name = call.function.name
                try:
                    arguments = json.loads(call.function.arguments or "{}") or {}
                except json.JSONDecodeError:
                    arguments = {}
                result = self.tools.run(name, arguments if isinstance(arguments, dict) else {})
                label = TOOL_LABELS.get(name, name)
                if label not in tools_used:
                    tools_used.append(label)
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": json.dumps(result, default=str, separators=(",", ":")),
                })

        raise RuntimeError("Agent did not finish")

    # ── Deterministic fallback ───────────────────────────────────────────────

    def _fallback_reply(self, message: str) -> AgentReply:
        analysis = self.tools.analysis
        text = message.lower()
        if not analysis.snapshot.courses:
            return AgentReply(
                content="I don't have any courses for you yet. Add your courses and assignments, and I can build your plan.",
                tools_used=["Courses"], ai_powered=False,
            )
        if any(word in text for word in ("score", "why", "recovery")):
            score = analysis.score
            top = [f.label for f in score.factors if f.points_lost > 0][:3]
            details = "; ".join(top) if top else "nothing is pulling it down right now"
            content = (
                f"Your Recovery Score is {score.score} ({score.band_label}). "
                f"The biggest factors: {details}. "
                "It's ARWA's planning metric, calculated from your grades, completion, study time, and deadlines."
            )
            return AgentReply(content=content, tools_used=["Recovery Score"], ai_powered=False)

        insight = engine.build_insight(analysis.snapshot, analysis.priorities, analysis.plan.days)
        unscheduled = analysis.plan.unscheduled
        extra = (f" Heads up: {len(unscheduled)} item(s) don't fit in your study time before they're due."
                 if unscheduled else "")
        return AgentReply(
            content=insight.message + extra + " (ARWA's AI is unavailable right now, so this answer comes straight from your plan.)",
            tools_used=["Recovery plan"], ai_powered=False,
        )
