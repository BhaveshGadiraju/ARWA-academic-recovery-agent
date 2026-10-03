"""Unit tests for the deterministic academic engine and planner (no network)."""

from datetime import date, datetime, time, timedelta
from typing import List, Optional

from backend.services import academic_engine as engine
from backend.services.domain import Assignment, Course, DayAvailability, StudentSnapshot, Wellness
from backend.services.planner import build_plan

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore

NOW = datetime(2026, 10, 5, 9, 0, tzinfo=ZoneInfo("America/New_York"))  # a Monday morning
TODAY = NOW.date()
CHEM = Course(id="c1", name="Organic Chemistry", code="CHEM 241", target_grade=85)
MATH = Course(id="c2", name="Linear Algebra", code="MATH 221")


def task(id: str, days: int, minutes: int, course: Course = CHEM, **extra) -> Assignment:
    return Assignment(id=id, title=f"Task {id}", due_date=TODAY + timedelta(days=days), estimated_minutes=minutes,
                      course_id=course.id, course_name=course.name, **extra)


def every_day(minutes: int, start: time = time(18, 0)):
    return {d: DayAvailability(weekday=d, minutes=minutes, start_time=start) for d in range(7)}


def snap(assignments: List[Assignment], availability=None, courses=(CHEM, MATH),
         wellness: Optional[Wellness] = None) -> StudentSnapshot:
    return StudentSnapshot(now=NOW, courses=list(courses), assignments=assignments,
                           availability=every_day(180) if availability is None else availability, wellness=wellness)


def analyze(s: StudentSnapshot):
    metrics = engine.compute_metrics(s)
    score = engine.compute_recovery_score(s, metrics)
    priorities = engine.rank_priorities(s)
    plan = build_plan(s, priorities, days=7)
    risks = engine.detect_risks(s, metrics, plan.unscheduled)
    return metrics, score, priorities, plan, risks


class TestRecoveryScore:
    def test_no_data_gives_no_score(self):
        s = StudentSnapshot(now=NOW)
        score = engine.compute_recovery_score(s, engine.compute_metrics(s))
        assert score.score is None and score.band == "not_enough_data"

    def test_light_week_with_good_grades_is_on_track(self):
        s = snap([
            task("a", 5, 60),
            task("g", -3, 60, completed=True, points_possible=100, points_earned=95),
        ])
        _, score, *_ = analyze(s)
        assert score.score >= 80 and score.band == "on_track"

    def test_overdue_work_lowers_score_and_is_explained(self):
        base = [task("a", 5, 60), task("g", -3, 60, completed=True, points_possible=100, points_earned=90)]
        _, before, *_ = analyze(snap(base))
        _, after, *_ = analyze(snap(base + [task("late", -1, 60)]))
        assert after.score < before.score
        assert any(f.key == "overdue" and f.points_lost > 0 for f in after.factors)

    def test_overload_scores_lower_than_light_week(self):
        light = snap([task("a", 5, 60)])
        heavy = snap([task(str(i), 2, 300) for i in range(5)], availability=every_day(60))
        assert analyze(heavy)[1].score < analyze(light)[1].score

    def test_score_stays_in_range(self):
        worst = snap([task(str(i), -i - 1, 600) for i in range(6)]
                     + [task("g", -9, 60, completed=True, points_possible=100, points_earned=10)],
                     availability={})
        score = analyze(worst)[1].score
        assert 0 <= score <= 100


class TestGrades:
    def test_performance_mapping_bounds(self):
        assert engine.performance_from_grade(40) == 0
        assert engine.performance_from_grade(95) == 100
        assert engine.performance_from_grade(100) == 100
        assert engine.performance_from_grade(20) == 0

    def test_course_grade_is_points_weighted(self):
        items = [
            task("q", -5, 30, completed=True, points_possible=10, points_earned=5),
            task("e", -2, 30, completed=True, points_possible=90, points_earned=81),
        ]
        assert engine.course_grade(CHEM.id, items) == 86.0

    def test_ungraded_course_has_no_grade(self):
        assert engine.course_grade(CHEM.id, [task("a", 3, 60)]) is None

    def test_logged_time_never_hides_incomplete_work(self):
        a = task("a", 3, 60, logged_minutes=200)
        assert a.remaining_minutes == 15
        assert task("b", 3, 60, completed=True).remaining_minutes == 0


class TestPriorities:
    def test_exam_tomorrow_beats_homework_next_week(self):
        s = snap([task("hw", 6, 60), task("exam", 1, 120, category="exam")])
        ranked = engine.rank_priorities(s)
        assert [p.assignment_id for p in ranked][:2] == ["exam", "hw"]

    def test_completed_work_is_not_prioritized(self):
        s = snap([task("done", 1, 60, completed=True), task("todo", 3, 60)])
        assert [p.assignment_id for p in engine.rank_priorities(s)] == ["todo"]


class TestPlanner:
    def test_blocks_fit_windows_and_respect_due_dates(self):
        s = snap([task("a", 1, 120), task("b", 3, 240, category="exam"), task("c", 6, 90, course=MATH)])
        plan = build_plan(s, engine.rank_priorities(s), days=7)
        by_id = {a.id: a for a in s.assignments}
        for day in plan.days:
            assert day.study_minutes <= day.window_minutes
            for block in day.blocks:
                if block.kind == "study":
                    assert block.assignment_id in by_id
                    assert day.date <= by_id[block.assignment_id].due_date
        assert plan.is_feasible

    def test_insufficient_time_is_reported_not_hidden(self):
        s = snap([task("big", 1, 600, category="exam")], availability=every_day(60))
        _, _, _, plan, risks = analyze(s)
        assert not plan.is_feasible
        assert plan.unscheduled[0].assignment_id == "big"
        assert any(r.kind == "insufficient_time" for r in risks)

    def test_overdue_work_does_not_take_a_whole_evening_from_an_upcoming_exam(self):
        s = snap([task("late", -2, 180), task("exam", 2, 360, category="exam")], availability=every_day(120))
        plan = build_plan(s, engine.rank_priorities(s), days=3)
        for day in plan.days[1:]:
            studied = {b.assignment_id for b in day.blocks if b.kind == "study"}
            assert studied == {"late", "exam"}

    def test_no_availability_schedules_nothing_and_flags_missing_data(self):
        s = snap([task("a", 2, 60)], availability={})
        _, _, _, plan, risks = analyze(s)
        assert all(not d.blocks for d in plan.days)
        assert any(r.kind == "missing_data" for r in risks)


class TestRisks:
    def test_overdue_and_exam_risks(self):
        s = snap([task("late", -2, 60), task("exam", 1, 120, category="exam")])
        kinds = {r.kind: r for r in analyze(s)[4]}
        assert "overdue" in kinds and "upcoming_exam" in kinds
        assert kinds["upcoming_exam"].severity == "critical"
        assert kinds["overdue"].assignment_id == "late"

    def test_low_grade_risk_for_course_below_target(self):
        s = snap([task("q", -4, 30, completed=True, points_possible=100, points_earned=60)])
        risks = analyze(s)[4]
        assert any(r.kind == "low_grade" and r.course_id == CHEM.id for r in risks)

    def test_risks_are_sorted_by_severity(self):
        s = snap([task("late", -2, 60), task("exam", 1, 120, category="exam"), task("hw", 4, 60)])
        order = [engine.SEVERITY_ORDER[r.severity] for r in analyze(s)[4]]
        assert order == sorted(order)


class TestInsight:
    def test_insight_keeps_course_code_casing(self):
        graded = task("q", -5, 30, course=CHEM, completed=True, points_possible=100, points_earned=60)
        s = snap([task("late", -2, 60), graded])
        _, _, priorities, plan, _ = analyze(s)
        message = engine.build_insight(s, priorities, plan.days).message
        assert "CHEM 241" in priorities[0].reason
        assert "chem 241" not in message
        assert engine.lower_first("Due tomorrow · MATH 221") == "due tomorrow · MATH 221"
