"""
ARWA insights service (business logic).

Loads the student's data through the repository, converts it into an engine
snapshot in the student's local time, and runs the deterministic engine and
planner. The API routes and the AI agent both use this service, so the
dashboard and ARWA's answers always agree.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Dict, List, Optional

from backend.services import academic_engine as engine
from backend.services.domain import Assignment, Course, DayAvailability, StudentSnapshot, Wellness
from backend.services.errors import NotFoundError
from backend.services.planner import build_plan
from backend.services.repository import AcademicRepository, Row, parse_timestamp
from models.insights import (
    CourseHealth,
    CourseTrend,
    Dashboard,
    MissedItem,
    Metric,
    PriorityItem,
    Progress,
    RecoveryPlan,
    RecoveryScore,
    Risk,
    SetupStatus,
    StudyDay,
    TrendPoint,
    WeeklyCompletion,
)

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python < 3.9
    from backports.zoneinfo import ZoneInfo  # type: ignore

logger = logging.getLogger(__name__)

WELLNESS_RELEVANT_DAYS = 14
TREND_DAYS = 14
HISTORY_DAYS = 30


@dataclass
class Analysis:
    """One full deterministic analysis of the student's current situation."""

    snapshot: StudentSnapshot
    profile: Row
    metrics: List[Metric]
    score: RecoveryScore
    priorities: List[PriorityItem]
    plan: RecoveryPlan
    risks: List[Risk]


def resolve_timezone(name: Optional[str]):
    """ZoneInfo for the profile timezone, falling back to UTC."""
    try:
        return ZoneInfo(name or "UTC")
    except Exception:
        return ZoneInfo("UTC")


def _parse_time(value: Optional[str]) -> time:
    """Parse 'HH:MM[:SS]' from Postgres into a time."""
    if not value:
        return time(18, 0)
    parts = [int(p) for p in value.split(":")[:2]]
    return time(parts[0], parts[1])


def _to_float(value) -> Optional[float]:
    return float(value) if value is not None else None


class InsightsService:
    """Builds dashboards, plans, course views, and progress from stored data."""

    def __init__(self, repo: AcademicRepository, clock: Optional[datetime] = None):
        self.repo = repo
        self._clock = clock

    # ── Snapshot loading ─────────────────────────────────────────────────────

    def local_now(self, profile: Row) -> datetime:
        """Current time in the student's timezone."""
        tz = resolve_timezone(profile.get("timezone"))
        if self._clock is not None:
            return self._clock.astimezone(tz)
        return datetime.now(tz)

    def load_snapshot(self) -> "tuple[StudentSnapshot, Row]":
        """Read everything the engine needs for the current semester."""
        profile = self.repo.get_profile()
        now = self.local_now(profile)

        semester = self.repo.current_semester()
        course_rows = self.repo.list_courses(semester["id"]) if semester else []
        courses = [
            Course(
                id=row["id"],
                name=row["name"],
                code=row.get("code"),
                credits=float(row.get("credits") or 3),
                target_grade=_to_float(row.get("target_grade")),
            )
            for row in course_rows
        ]
        course_ids = {c.id for c in courses}

        logged: Dict[str, int] = defaultdict(int)
        for session in self.repo.list_study_sessions():
            logged[session["assignment_id"]] += int(session["minutes"])

        assignments = [
            self._to_assignment(row, logged)
            for row in self.repo.list_assignments()
            if row.get("course_id") is None or row.get("course_id") in course_ids
        ]

        availability = {
            int(row["weekday"]): DayAvailability(
                weekday=int(row["weekday"]),
                minutes=int(row["minutes"]),
                start_time=_parse_time(row.get("start_time")),
            )
            for row in self.repo.list_availability()
        }

        wellness = None
        recent = self.repo.list_wellness(limit=1)
        if recent:
            created = parse_timestamp(recent[0].get("created_at"))
            if created is None or now - created <= timedelta(days=WELLNESS_RELEVANT_DAYS):
                wellness = Wellness(
                    stress_level=int(recent[0]["stress_level"]),
                    sleep_hours=_to_float(recent[0].get("sleep_hours")),
                    energy_level=recent[0].get("energy_level"),
                    created_at=created,
                )

        snapshot = StudentSnapshot(
            now=now, courses=courses, assignments=assignments, availability=availability, wellness=wellness,
        )
        return snapshot, profile

    @staticmethod
    def _to_assignment(row: Row, logged: Dict[str, int]) -> Assignment:
        return Assignment(
            id=row["id"],
            title=row["title"],
            due_date=date.fromisoformat(row["due_date"]),
            estimated_minutes=int(round(float(row.get("estimated_hours") or 0) * 60)),
            category=row.get("category") or "homework",
            course_id=row.get("course_id"),
            course_name=row.get("course"),
            completed=bool(row.get("completed")),
            completed_at=parse_timestamp(row.get("completed_at")),
            points_possible=_to_float(row.get("points_possible")),
            points_earned=_to_float(row.get("points_earned")),
            logged_minutes=logged.get(row["id"], 0),
        )

    # ── Analysis ─────────────────────────────────────────────────────────────

    def analyze(self, plan_days: int = 7) -> Analysis:
        """Run the full deterministic pipeline on fresh data."""
        snapshot, profile = self.load_snapshot()
        metrics = engine.compute_metrics(snapshot)
        score = engine.compute_recovery_score(snapshot, metrics)
        priorities = engine.rank_priorities(snapshot)
        plan = build_plan(snapshot, priorities, days=plan_days)
        risks = engine.detect_risks(snapshot, metrics, plan.unscheduled)
        return Analysis(snapshot, profile, metrics, score, priorities, plan, risks)

    def dashboard(self) -> Dashboard:
        """Home screen data. Also records today's Recovery Score for trends."""
        result = self.analyze()
        snapshot = result.snapshot
        trend = self._record_and_load_trend(result)

        previous = [p for p in trend if p.date < snapshot.today]
        if result.score.score is not None and previous:
            result.score.previous_score = previous[-1].score
            result.score.delta = result.score.score - previous[-1].score

        plan_today = result.plan.days[0] if result.plan.days else None
        return Dashboard(
            generated_at=snapshot.now,
            setup=SetupStatus(
                onboarding_completed=bool(result.profile.get("onboarding_completed")),
                has_courses=bool(snapshot.courses),
                has_assignments=bool(snapshot.assignments),
                has_availability=any(d.minutes > 0 for d in snapshot.availability.values()),
                has_grades=any(a.is_graded for a in snapshot.assignments),
            ),
            score=result.score,
            metrics=result.metrics,
            today=engine.today_overview(snapshot, result.metrics),
            risks=result.risks,
            priorities=result.priorities[:5],
            plan_today=plan_today,
            insight=engine.build_insight(snapshot, result.priorities, result.plan.days),
            courses=[engine.course_health(c, snapshot) for c in snapshot.courses],
            trend=trend,
        )

    def _record_and_load_trend(self, result: Analysis) -> List[TrendPoint]:
        """Upsert today's snapshot and return recent history."""
        today = result.snapshot.today
        if result.score.score is not None:
            try:
                planned_today = result.plan.days[0].study_minutes if result.plan.days else 0
                self.repo.upsert_snapshot(
                    today,
                    result.score.score,
                    metrics={**{m.key: m.value for m in result.metrics}, "planned_today_minutes": planned_today},
                    factors=[f.model_dump() for f in result.score.factors],
                )
            except Exception:
                logger.exception("Failed to record recovery snapshot")
        rows = self.repo.list_snapshots(since=today - timedelta(days=TREND_DAYS - 1))
        return [TrendPoint(date=date.fromisoformat(r["snapshot_date"]), score=int(r["score"])) for r in rows]

    # ── Courses ──────────────────────────────────────────────────────────────

    def course_detail(self, course_id: str) -> Dict:
        """Health, assignments, risks, and a recommended next step for one course."""
        course_row = self.repo.get_course(course_id)
        result = self.analyze()
        course = result.snapshot.course(course_id)
        if course is None:
            course = Course(
                id=course_row["id"], name=course_row["name"], code=course_row.get("code"),
                credits=float(course_row.get("credits") or 3), target_grade=_to_float(course_row.get("target_grade")),
            )
        health = engine.course_health(course, result.snapshot)
        risks = [r for r in result.risks if r.course_id == course_id
                 or (r.assignment_id and any(a.id == r.assignment_id and a.course_id == course_id
                                             for a in result.snapshot.assignments))]
        top = next((p for p in result.priorities if p.course_id == course_id), None)
        if risks:
            action = risks[0].action
        elif top:
            action = f"Next up: {top.title} ({engine.lower_first(top.reason)})."
        else:
            action = "Nothing pending in this course. Add new assignments as they're posted."
        return {
            "course": course_row,
            "health": health,
            "assignments": self.repo.list_assignments(course_id=course_id),
            "risks": risks,
            "recommended_action": action,
        }

    def course_health_list(self) -> List[CourseHealth]:
        """Health for every course in the current semester."""
        snapshot, _ = self.load_snapshot()
        return [engine.course_health(c, snapshot) for c in snapshot.courses]

    # ── Progress ─────────────────────────────────────────────────────────────

    def progress(self) -> Progress:
        """History for the Progress screen."""
        snapshot, _ = self.load_snapshot()
        today = snapshot.today
        tz = snapshot.now.tzinfo

        snapshots = self.repo.list_snapshots(since=today - timedelta(days=HISTORY_DAYS - 1))
        planned_by_day = {
            r["snapshot_date"]: (r.get("metrics") or {}).get("planned_today_minutes") for r in snapshots
        }
        sessions = self.repo.list_study_sessions(since=today - timedelta(days=13))
        studied: Dict[str, int] = defaultdict(int)
        for s in sessions:
            studied[s["session_date"]] += int(s["minutes"])
        study_days = []
        for offset in range(13, -1, -1):
            day = (today - timedelta(days=offset)).isoformat()
            study_days.append(StudyDay(
                date=day, studied_minutes=studied.get(day, 0), planned_minutes=planned_by_day.get(day),
            ))

        week_start = today - timedelta(days=today.weekday())
        weeks = {week_start - timedelta(weeks=i): [0, 0] for i in range(5, -1, -1)}
        missed: List[MissedItem] = []
        for a in snapshot.assignments:
            if a.completed and a.completed_at:
                done_day = a.completed_at.astimezone(tz).date()
                bucket = done_day - timedelta(days=done_day.weekday())
                if bucket in weeks:
                    weeks[bucket][0] += 1
                    weeks[bucket][1] += int(done_day <= a.due_date)
                if done_day > a.due_date and (today - a.due_date).days <= HISTORY_DAYS:
                    missed.append(MissedItem(
                        assignment_id=a.id, title=a.title, course_name=a.course_name,
                        due_date=a.due_date, status="late",
                    ))
            elif not a.completed and a.due_date < today:
                missed.append(MissedItem(
                    assignment_id=a.id, title=a.title, course_name=a.course_name, due_date=a.due_date, status="overdue",
                ))
        missed.sort(key=lambda m: m.due_date, reverse=True)

        course_trends = []
        for course in snapshot.courses:
            graded = sorted((a for a in snapshot.assignments if a.course_id == course.id and a.is_graded),
                            key=lambda a: a.due_date)
            earned = possible = 0.0
            points = []
            for a in graded:
                earned += float(a.points_earned)
                possible += float(a.points_possible)
                points.append({"date": a.due_date.isoformat(), "grade": round(100 * earned / possible, 1), "title": a.title})
            course_trends.append(CourseTrend(course_id=course.id, name=course.code or course.name, points=points))

        this_week = [d for d in study_days if date.fromisoformat(str(d.date)) >= week_start]
        return Progress(
            score_history=[TrendPoint(date=date.fromisoformat(r["snapshot_date"]), score=int(r["score"])) for r in snapshots],
            study_days=study_days,
            weekly_completion=[WeeklyCompletion(week_start=k, completed=v[0], on_time=v[1]) for k, v in weeks.items()],
            missed=missed,
            course_trends=course_trends,
            totals={
                "completed": sum(1 for a in snapshot.assignments if a.completed),
                "pending": sum(1 for a in snapshot.assignments if not a.completed),
                "overdue": sum(1 for m in missed if m.status == "overdue"),
                "studied_minutes_this_week": sum(d.studied_minutes for d in this_week),
                "planned_minutes_this_week": sum(d.planned_minutes or 0 for d in this_week),
            },
        )
