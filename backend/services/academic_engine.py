"""
ARWA deterministic academic engine.

Turns a StudentSnapshot into grades, academic health metrics, the Recovery
Score, ranked priorities, and risks. Every value here is calculated from the
student's stored data with documented formulas; the AI layer only explains
these results and never produces them.

Recovery Score (0-100, higher = more manageable):

    weighted average of four components (each 0-100, higher is better)
        Performance        30%   overall grade mapped from 40% -> 0 to 95% -> 100
        Completion         20%   share of past-due assignments that are done
        Capacity           30%   available study time / work due in 7 days
        Deadline headroom  20%   100 - Deadline Pressure
    minus an overdue penalty of 5 points per overdue item (max 15).

Components without data (e.g. no graded work yet) are left out and the
remaining weights are re-normalised, so missing data never fakes a low score.
"""

from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple

from backend.services.domain import Assignment, Course, DayAvailability, StudentSnapshot
from models.insights import (
    CourseHealth,
    Insight,
    Metric,
    NextDue,
    PlanDay,
    PriorityItem,
    RecoveryScore,
    Risk,
    ScoreFactor,
    TodayOverview,
    UnscheduledWork,
)

SCORE_WEIGHTS: Dict[str, float] = {
    "performance": 0.30,
    "completion": 0.20,
    "capacity": 0.30,
    "deadline": 0.20,
}
OVERDUE_PENALTY_PER_ITEM = 5
OVERDUE_PENALTY_MAX = 15

# Pending hours in the next 7 days that count as a 100% workload.
HEAVY_WEEK_HOURS = 20.0
# Pending hours in one course over 7 days that count as a full course load.
HEAVY_COURSE_WEEK_HOURS = 8.0
DEFAULT_TARGET_GRADE = 85.0

CATEGORY_WEIGHT: Dict[str, float] = {
    "exam": 1.0,
    "project": 0.8,
    "paper": 0.8,
    "quiz": 0.6,
    "lab": 0.5,
    "homework": 0.5,
    "other": 0.4,
    "reading": 0.3,
}
CATEGORY_LABEL: Dict[str, str] = {
    "exam": "exam",
    "project": "project",
    "paper": "paper",
    "quiz": "quiz",
    "lab": "lab",
    "homework": "homework",
    "other": "task",
    "reading": "reading",
}

SEVERITY_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


# ── Small helpers ────────────────────────────────────────────────────────────

def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    """Limit a value to [low, high]."""
    return max(low, min(high, value))


def format_minutes(minutes: int) -> str:
    """Render minutes as '45m', '2h' or '2h 30m'."""
    minutes = int(round(minutes))
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    if hours:
        return f"{hours}h"
    return f"{mins}m"


def format_clock(hhmm: str) -> str:
    """Render '18:05' as '6:05 PM'."""
    hour, minute = (int(part) for part in hhmm.split(":"))
    suffix = "AM" if hour < 12 else "PM"
    return f"{hour % 12 or 12}:{minute:02d} {suffix}"


def lower_first(text: str) -> str:
    """Lowercase only the first character, so a reason reads mid-sentence without mangling course codes."""
    return text[:1].lower() + text[1:]


def format_date(day: date) -> str:
    """Render a date for people, e.g. 'Sun, Oct 4'."""
    return f"{day.strftime('%a, %b')} {day.day}"


def days_until(due: date, today: date) -> int:
    """Calendar days from today to a due date (negative when overdue)."""
    return (due - today).days


def describe_due(due: date, today: date) -> str:
    """Human phrase for a due date relative to today."""
    days = days_until(due, today)
    if days < -1:
        return f"{-days} days overdue"
    if days == -1:
        return "1 day overdue"
    if days == 0:
        return "due today"
    if days == 1:
        return "due tomorrow"
    if days < 7:
        return f"due {due.strftime('%A')}"
    return f"due {due.strftime('%b')} {due.day}"


def performance_from_grade(grade: float) -> int:
    """Map a grade percentage onto the 0-100 performance scale."""
    return int(round(clamp((grade - 40.0) / 55.0 * 100.0)))


def incomplete(assignments: List[Assignment]) -> List[Assignment]:
    """Assignments that still need work."""
    return [a for a in assignments if not a.completed]


def overdue(snapshot: StudentSnapshot) -> List[Assignment]:
    """Incomplete assignments whose due date has passed."""
    return [a for a in incomplete(snapshot.assignments) if a.due_date < snapshot.today]


# ── Time ─────────────────────────────────────────────────────────────────────

def window_minutes_left_today(now: datetime, day: Optional[DayAvailability]) -> int:
    """Minutes of today's study window that have not passed yet."""
    if day is None or day.minutes <= 0:
        return 0
    start = now.replace(hour=day.start_time.hour, minute=day.start_time.minute, second=0, microsecond=0)
    end = start + timedelta(minutes=day.minutes)
    if now <= start:
        return day.minutes
    if now >= end:
        return 0
    return int((end - now).total_seconds() // 60)


def available_minutes(snapshot: StudentSnapshot, days: int) -> int:
    """Study minutes available from now through the next `days` calendar days (today included)."""
    total = window_minutes_left_today(snapshot.now, snapshot.availability.get(snapshot.today.weekday()))
    for offset in range(1, days):
        day = snapshot.today + timedelta(days=offset)
        availability = snapshot.availability.get(day.weekday())
        total += availability.minutes if availability else 0
    return total


def required_minutes(snapshot: StudentSnapshot, days: int) -> int:
    """Remaining work on incomplete items due within `days` days, including overdue work."""
    horizon = snapshot.today + timedelta(days=days - 1)
    return sum(a.remaining_minutes for a in incomplete(snapshot.assignments) if a.due_date <= horizon)


# ── Grades ───────────────────────────────────────────────────────────────────

def course_grade(course_id: Optional[str], assignments: List[Assignment]) -> Optional[float]:
    """Points-based course grade from graded work, or None if nothing is graded."""
    graded = [a for a in assignments if a.course_id == course_id and a.is_graded]
    possible = sum(float(a.points_possible) for a in graded)
    if possible <= 0:
        return None
    earned = sum(float(a.points_earned) for a in graded)
    return round(100.0 * earned / possible, 1)


def course_trend(course_id: Optional[str], assignments: List[Assignment]) -> Optional[float]:
    """Average of the two most recent graded items minus the average of earlier ones."""
    graded = sorted(
        (a for a in assignments if a.course_id == course_id and a.is_graded),
        key=lambda a: a.due_date,
    )
    if len(graded) < 4:
        return None
    recent = [a.grade_percent for a in graded[-2:]]
    earlier = [a.grade_percent for a in graded[:-2]]
    return round(sum(recent) / len(recent) - sum(earlier) / len(earlier), 1)


def overall_grade(snapshot: StudentSnapshot) -> Optional[float]:
    """Credit-weighted average of course grades that have graded work."""
    weighted, credits = 0.0, 0.0
    for course in snapshot.courses:
        grade = course_grade(course.id, snapshot.assignments)
        if grade is not None:
            weighted += grade * course.credits
            credits += course.credits
    if credits == 0:
        return None
    return round(weighted / credits, 1)


def completion_rate(assignments: List[Assignment], today: date) -> Optional[int]:
    """Share of past-due assignments that are complete, or None if nothing is past due."""
    past_due = [a for a in assignments if a.due_date < today]
    if not past_due:
        return None
    done = sum(1 for a in past_due if a.completed)
    return int(round(100.0 * done / len(past_due)))


# ── Metrics ──────────────────────────────────────────────────────────────────

def compute_metrics(snapshot: StudentSnapshot) -> List[Metric]:
    """Academic health metrics. Each is backed by a documented calculation."""
    pending_week = required_minutes(snapshot, 7)
    available_week = available_minutes(snapshot, 7)
    due_soon = required_minutes(snapshot, 3)
    available_soon = available_minutes(snapshot, 3)
    grade = overall_grade(snapshot)

    workload = int(round(clamp(pending_week / 60.0 / HEAVY_WEEK_HOURS * 100.0)))
    workload_level = "Light" if workload < 35 else "Moderate" if workload < 70 else "Heavy"

    pressure = _deadline_pressure(due_soon, available_soon)
    pressure_level = "Low" if pressure < 35 else "Moderate" if pressure < 65 else "High"

    capacity = _capacity(available_week, pending_week)
    capacity_level = "Strong" if capacity >= 90 else "Tight" if capacity >= 60 else "Overloaded"

    performance = performance_from_grade(grade) if grade is not None else None
    if performance is None:
        performance_level, performance_summary = "No grades yet", "Add points earned to see performance"
    else:
        performance_level = "Strong" if performance >= 75 else "Fair" if performance >= 50 else "Low"
        performance_summary = f"{grade:.1f}% overall across graded work"

    return [
        Metric(
            key="workload",
            label="Workload",
            value=workload,
            level=workload_level,
            summary=f"{format_minutes(pending_week)} of work due in the next 7 days",
            meaning=f"Pending work due within 7 days. {HEAVY_WEEK_HOURS:.0f}h or more counts as 100.",
            higher_is_better=False,
        ),
        Metric(
            key="deadline_pressure",
            label="Deadline Pressure",
            value=pressure,
            level=pressure_level,
            summary=f"{format_minutes(due_soon)} due in 3 days vs {format_minutes(available_soon)} available",
            meaning="Work due in the next 3 days compared with study time in those days. 75 means it exactly fills your time.",
            higher_is_better=False,
        ),
        Metric(
            key="performance",
            label="Performance",
            value=performance,
            level=performance_level,
            summary=performance_summary,
            meaning="Credit-weighted grade across courses, scaled so 40% maps to 0 and 95%+ maps to 100.",
            higher_is_better=True,
        ),
        Metric(
            key="capacity",
            label="Capacity",
            value=capacity,
            level=capacity_level,
            summary=f"{format_minutes(available_week)} available vs {format_minutes(pending_week)} needed this week",
            meaning="Study time available in the next 7 days as a share of the work due in that time (capped at 100).",
            higher_is_better=True,
        ),
    ]


def _deadline_pressure(due_minutes: int, available: int) -> int:
    """75 x (work due in 3 days / time available in 3 days), capped at 100."""
    if due_minutes <= 0:
        return 0
    if available <= 0:
        return 100
    return int(round(clamp(75.0 * due_minutes / available)))


def _capacity(available: int, required: int) -> int:
    """100 x available / required, capped at 100; 100 when nothing is due."""
    if required <= 0:
        return 100
    return int(round(clamp(100.0 * available / required)))


def metric_value(metrics: List[Metric], key: str) -> Optional[int]:
    """Fetch a metric's value by key."""
    return next((m.value for m in metrics if m.key == key), None)


# ── Recovery Score ───────────────────────────────────────────────────────────

def compute_recovery_score(snapshot: StudentSnapshot, metrics: List[Metric]) -> RecoveryScore:
    """Weighted, transparent Recovery Score with a per-factor breakdown."""
    if not snapshot.courses and not snapshot.assignments:
        return RecoveryScore(
            score=None,
            band="not_enough_data",
            band_label="Not enough data",
            headline="Add your courses and assignments so ARWA can calculate your Recovery Score.",
            factors=[],
        )

    grade = overall_grade(snapshot)
    completion = completion_rate(snapshot.assignments, snapshot.today)
    capacity = metric_value(metrics, "capacity")
    pressure = metric_value(metrics, "deadline_pressure") or 0
    overdue_items = overdue(snapshot)

    components: Dict[str, Optional[int]] = {
        "performance": performance_from_grade(grade) if grade is not None else None,
        "completion": completion if completion is not None else 100,
        "capacity": capacity,
        "deadline": 100 - pressure,
    }
    active = {k: v for k, v in components.items() if v is not None}
    total_weight = sum(SCORE_WEIGHTS[k] for k in active)
    weights = {k: SCORE_WEIGHTS[k] / total_weight for k in active}

    base = sum(weights[k] * active[k] for k in active)
    penalty = min(OVERDUE_PENALTY_MAX, OVERDUE_PENALTY_PER_ITEM * len(overdue_items))
    score = int(round(clamp(base - penalty)))

    factors = _score_factors(snapshot, metrics, components, weights, grade, completion, overdue_items, penalty)
    band, band_label = _score_band(score)
    return RecoveryScore(
        score=score,
        band=band,
        band_label=band_label,
        headline=_score_headline(score, factors),
        factors=factors,
    )


def _score_band(score: int) -> Tuple[str, str]:
    """Bucket a score into a named band."""
    if score >= 80:
        return "on_track", "On track"
    if score >= 65:
        return "manageable", "Manageable"
    if score >= 45:
        return "under_pressure", "Under pressure"
    return "needs_recovery", "Needs recovery"


def _score_factors(
    snapshot: StudentSnapshot,
    metrics: List[Metric],
    components: Dict[str, Optional[int]],
    weights: Dict[str, float],
    grade: Optional[float],
    completion: Optional[int],
    overdue_items: List[Assignment],
    penalty: int,
) -> List[ScoreFactor]:
    """Explain each component in plain language, ordered by points lost."""
    pending_week = required_minutes(snapshot, 7)
    available_week = available_minutes(snapshot, 7)
    due_soon = required_minutes(snapshot, 3)
    factors: List[ScoreFactor] = []

    def lost(key: str) -> int:
        value = components.get(key)
        if value is None or key not in weights:
            return 0
        return int(round(weights[key] * (100 - value)))

    perf = components["performance"]
    if perf is None:
        factors.append(ScoreFactor(
            key="performance", label="No graded work yet",
            detail="Record points earned on assignments so grades can count toward your score.",
            impact="neutral", value=None, weight=0.0, points_lost=0,
        ))
    else:
        label = (
            f"Strong grades ({grade:.0f}% overall)" if perf >= 75
            else f"Grades are fair ({grade:.0f}% overall)" if perf >= 50
            else f"Grades need attention ({grade:.0f}% overall)"
        )
        factors.append(ScoreFactor(
            key="performance", label=label,
            detail="Credit-weighted grade across your graded work.",
            impact="positive" if perf >= 75 else "neutral" if perf >= 50 else "negative",
            value=perf, weight=round(weights["performance"], 2), points_lost=lost("performance"),
        ))

    comp = components["completion"]
    if completion is None:
        comp_label, comp_detail = "Nothing past due yet", "Completion counts once assignments reach their due date."
    else:
        comp_label = (
            f"Strong assignment completion ({completion}%)" if completion >= 90
            else f"Assignment completion is {completion}%"
        )
        comp_detail = "Share of past-due assignments you have completed."
    factors.append(ScoreFactor(
        key="completion", label=comp_label, detail=comp_detail,
        impact="positive" if comp >= 90 else "neutral" if comp >= 70 else "negative",
        value=comp, weight=round(weights["completion"], 2), points_lost=lost("completion"),
    ))

    cap = components["capacity"] or 0
    if pending_week == 0:
        cap_label = "No work due in the next 7 days"
    elif cap >= 90:
        cap_label = "Enough study time for this week's work"
    else:
        cap_label = f"Limited study time ({format_minutes(available_week)} for {format_minutes(pending_week)} of work)"
    factors.append(ScoreFactor(
        key="capacity", label=cap_label,
        detail="Available study time in the next 7 days compared with work due in that time.",
        impact="positive" if cap >= 90 else "neutral" if cap >= 60 else "negative",
        value=cap, weight=round(weights["capacity"], 2), points_lost=lost("capacity"),
    ))

    headroom = components["deadline"]
    pressure_level = next(m.level for m in metrics if m.key == "deadline_pressure")
    if due_soon == 0:
        deadline_label = "No deadlines in the next 3 days"
    elif pressure_level == "High":
        deadline_label = f"Heavy deadline pressure ({format_minutes(due_soon)} due in 3 days)"
    else:
        deadline_label = f"{pressure_level} deadline pressure ({format_minutes(due_soon)} due in 3 days)"
    factors.append(ScoreFactor(
        key="deadline", label=deadline_label,
        detail="Work due in the next 3 days compared with your study time in those days.",
        impact="positive" if headroom >= 65 else "neutral" if headroom >= 35 else "negative",
        value=headroom, weight=round(weights["deadline"], 2), points_lost=lost("deadline"),
    ))

    count = len(overdue_items)
    factors.append(ScoreFactor(
        key="overdue",
        label="No overdue work" if count == 0 else f"{count} overdue assignment{'s' if count != 1 else ''}",
        detail=f"Each overdue item subtracts {OVERDUE_PENALTY_PER_ITEM} points (up to {OVERDUE_PENALTY_MAX}).",
        impact="positive" if count == 0 else "negative",
        value=None, weight=0.0, points_lost=penalty,
    ))

    factors.sort(key=lambda f: (-f.points_lost, f.impact != "negative"))
    return factors


def _score_headline(score: int, factors: List[ScoreFactor]) -> str:
    """One-sentence summary driven by the biggest negative factor."""
    worst = next((f for f in factors if f.impact == "negative" and f.points_lost > 0), None)
    concern = {
        "overdue": "overdue work is pulling your score down",
        "capacity": "you have less study time than this week's work needs",
        "deadline": "several deadlines are close together",
        "performance": "your grades need attention",
        "completion": "some past assignments were not completed",
    }
    if worst is None:
        if score >= 80:
            return "You're on track. Keep your current pace."
        return "You're in a manageable spot. Stay ahead of upcoming deadlines."
    reason = concern.get(worst.key, worst.label.lower())
    if score >= 80:
        return f"You're doing well, but {reason}."
    if score >= 65:
        return f"Manageable, but {reason}."
    if score >= 45:
        return f"You're under pressure: {reason}."
    return f"Time to regroup: {reason}. Focus on the plan below."


# ── Priorities ───────────────────────────────────────────────────────────────

def _urgency(days: int) -> float:
    """Deadline urgency from 1.0 (overdue) decaying with time."""
    if days < 0:
        return 1.0
    table = {0: 0.95, 1: 0.85, 2: 0.72, 3: 0.6}
    if days in table:
        return table[days]
    if days <= 7:
        return 0.6 - (days - 3) * 0.08
    return max(0.05, 0.28 - (days - 7) * 0.02)


def rank_priorities(snapshot: StudentSnapshot) -> List[PriorityItem]:
    """Order incomplete work: 60% deadline urgency, 25% item weight, 15% course need."""
    items: List[PriorityItem] = []
    for a in incomplete(snapshot.assignments):
        days = days_until(a.due_date, snapshot.today)
        course = snapshot.course(a.course_id)
        grade = course_grade(a.course_id, snapshot.assignments) if a.course_id else None
        target = (course.target_grade if course and course.target_grade else DEFAULT_TARGET_GRADE)
        need = clamp((target - grade) / 30.0, 0.0, 1.0) if grade is not None else 0.0
        importance = CATEGORY_WEIGHT.get(a.category, 0.4)
        score = 0.6 * _urgency(days) + 0.25 * importance + 0.15 * need

        due_phrase = describe_due(a.due_date, snapshot.today)
        reasons = [due_phrase[0].upper() + due_phrase[1:]]
        if a.category in ("exam", "project", "paper"):
            reasons.append(f"{CATEGORY_LABEL[a.category]} weighs heavily")
        if grade is not None and grade < target:
            reasons.append(f"{course.display_name if course else 'course'} grade {grade:.0f}% is below your {target:.0f}% target")
        items.append(PriorityItem(
            rank=0,
            assignment_id=a.id,
            title=a.title,
            course_id=a.course_id,
            course_name=a.course_name,
            category=a.category,
            due_date=a.due_date,
            days_until_due=days,
            remaining_minutes=a.remaining_minutes,
            score=round(score, 3),
            reason=" · ".join(reasons),
        ))

    items.sort(key=lambda p: (-p.score, p.due_date, p.title))
    for index, item in enumerate(items, start=1):
        item.rank = index
    return items


# ── Risks ────────────────────────────────────────────────────────────────────

def detect_risks(
    snapshot: StudentSnapshot,
    metrics: List[Metric],
    unscheduled: List[UnscheduledWork],
) -> List[Risk]:
    """Rule-based risk detection. Each risk cites the data that triggered it."""
    risks: List[Risk] = []
    today = snapshot.today

    for a in overdue(snapshot):
        late = -days_until(a.due_date, today)
        severity = "critical" if a.category == "exam" or late > 7 else "high"
        risks.append(Risk(
            id=f"overdue:{a.id}", severity=severity, kind="overdue",
            title=f"{a.title} is overdue",
            reason=f"It was due {format_date(a.due_date)} ({late} day{'s' if late != 1 else ''} ago) and is not marked complete.",
            action=f"Finish and submit {a.title} first, or mark it complete if you already turned it in.",
            course_id=a.course_id, course_name=a.course_name, assignment_id=a.id,
            data={"due_date": a.due_date.isoformat(), "days_overdue": late, "remaining_minutes": a.remaining_minutes},
        ))

    for a in incomplete(snapshot.assignments):
        days = days_until(a.due_date, today)
        if a.category == "exam" and 0 <= days <= 3:
            risks.append(Risk(
                id=f"exam:{a.id}", severity="critical" if days <= 1 else "high", kind="upcoming_exam",
                title=f"{a.title} is {describe_due(a.due_date, today)}",
                reason=f"Major exam in {days} day{'s' if days != 1 else ''} with about {format_minutes(a.remaining_minutes)} of prep left.",
                action=f"Schedule review for {a.title} before anything lower priority.",
                course_id=a.course_id, course_name=a.course_name, assignment_id=a.id,
                data={"due_date": a.due_date.isoformat(), "days_until_due": days, "remaining_minutes": a.remaining_minutes},
            ))

    for work in unscheduled:
        risks.append(Risk(
            id=f"no_time:{work.assignment_id}", severity="high", kind="insufficient_time",
            title=f"Not enough time for {work.title}",
            reason=(
                f"About {format_minutes(work.unscheduled_minutes)} of {work.title} does not fit into your study "
                f"time before it's due on {format_date(work.due_date)}."
            ),
            action="Add study time before the deadline, lower the estimate if it's too high, or start it in a free gap.",
            course_name=work.course_name, assignment_id=work.assignment_id,
            data={"due_date": work.due_date.isoformat(), "unscheduled_minutes": work.unscheduled_minutes},
        ))

    risks.extend(_deadline_cluster_risks(snapshot))

    capacity = metric_value(metrics, "capacity")
    pending_week = required_minutes(snapshot, 7)
    available_week = available_minutes(snapshot, 7)
    if capacity is not None and pending_week > 0 and capacity < 100:
        severity = "critical" if capacity < 40 else "high" if capacity < 70 else "moderate"
        risks.append(Risk(
            id="capacity:week", severity=severity, kind="workload",
            title="This week's work exceeds your study time",
            reason=f"{format_minutes(pending_week)} of work is due in 7 days, but you have {format_minutes(available_week)} of study time.",
            action="Follow the plan in priority order and add study time if you can. Lower-priority items may need to slip.",
            data={"required_minutes": pending_week, "available_minutes": available_week, "capacity": capacity},
        ))

    for course in snapshot.courses:
        risks.extend(_course_risks(course, snapshot))

    if snapshot.assignments and not any(d.minutes > 0 for d in snapshot.availability.values()):
        risks.append(Risk(
            id="setup:availability", severity="moderate", kind="missing_data",
            title="No study time set",
            reason="ARWA can't schedule your work without knowing when you're free to study.",
            action="Add your weekly study time in Settings.",
            data={},
        ))

    wellness = snapshot.wellness
    if wellness and wellness.stress_level >= 8 and (capacity or 0) < 70 and pending_week > 0:
        risks.append(Risk(
            id="wellness:stress", severity="moderate", kind="wellness",
            title="High stress with a heavy week",
            reason=f"You reported stress at {wellness.stress_level}/10 while this week's work is above your available time.",
            action="ARWA shortened your study blocks. Protect breaks and sleep, and focus only on the top priorities.",
            data={"stress_level": wellness.stress_level, "capacity": capacity},
        ))

    risks.sort(key=lambda r: (SEVERITY_ORDER[r.severity], r.title))
    return risks


def _deadline_cluster_risks(snapshot: StudentSnapshot) -> List[Risk]:
    """Flag 3+ incomplete items due within any 48-hour window in the next 7 days."""
    today = snapshot.today
    upcoming = sorted(
        (a for a in incomplete(snapshot.assignments) if 0 <= days_until(a.due_date, today) <= 7),
        key=lambda a: a.due_date,
    )
    best: List[Assignment] = []
    for a in upcoming:
        window = [b for b in upcoming if a.due_date <= b.due_date <= a.due_date + timedelta(days=1)]
        if len(window) > len(best):
            best = window
    if len(best) < 3:
        return []
    start = best[0].due_date
    minutes = sum(a.remaining_minutes for a in best)
    return [Risk(
        id=f"cluster:{start.isoformat()}",
        severity="high" if len(best) >= 4 else "moderate",
        kind="deadline_cluster",
        title=f"{len(best)} deadlines around {start.strftime('%A')}",
        reason=f"{len(best)} items totalling {format_minutes(minutes)} are due within 48 hours of {format_date(start)}.",
        action="Start the larger items early instead of the night before.",
        data={"items": [a.title for a in best], "start_date": start.isoformat(), "total_minutes": minutes},
    )]


def _course_risks(course: Course, snapshot: StudentSnapshot) -> List[Risk]:
    """Low-grade and declining-grade risks for one course."""
    risks: List[Risk] = []
    grade = course_grade(course.id, snapshot.assignments)
    if grade is not None:
        target = course.target_grade or DEFAULT_TARGET_GRADE
        if grade < 60:
            severity = "critical"
        elif grade < 70:
            severity = "high"
        elif grade < target:
            severity = "moderate"
        else:
            severity = None
        if severity:
            risks.append(Risk(
                id=f"grade:{course.id}", severity=severity, kind="low_grade",
                title=f"{course.display_name} grade is {grade:.0f}%",
                reason=f"Your graded work in {course.name} averages {grade:.1f}%, below your {target:.0f}% target.",
                action=f"Prioritise upcoming {course.display_name} work and review recent mistakes.",
                course_id=course.id, course_name=course.name,
                data={"grade": grade, "target_grade": target},
            ))

    trend = course_trend(course.id, snapshot.assignments)
    if trend is not None and trend <= -10:
        risks.append(Risk(
            id=f"trend:{course.id}", severity="high" if trend <= -20 else "moderate", kind="declining_grades",
            title=f"{course.display_name} grades are slipping",
            reason=f"Your two most recent graded items are {abs(trend):.0f} points below your earlier average.",
            action=f"Look at what changed in {course.display_name} and give it extra time this week.",
            course_id=course.id, course_name=course.name,
            data={"trend_points": trend},
        ))
    return risks


# ── Courses ──────────────────────────────────────────────────────────────────

def course_health(course: Course, snapshot: StudentSnapshot) -> CourseHealth:
    """Per-course health: 60% grade, 20% completion, 20% inverse weekly load."""
    today = snapshot.today
    course_items = [a for a in snapshot.assignments if a.course_id == course.id]
    pending = incomplete(course_items)
    pending_week = sum(a.remaining_minutes for a in pending if a.due_date <= today + timedelta(days=6))
    grade = course_grade(course.id, snapshot.assignments)
    completion = completion_rate(course_items, today)
    load = clamp(pending_week / 60.0 / HEAVY_COURSE_WEEK_HOURS * 100.0)

    parts = {
        "grade": (0.6, performance_from_grade(grade) if grade is not None else None),
        "completion": (0.2, completion if completion is not None else 100),
        "load": (0.2, 100 - load),
    }
    active = {k: v for k, v in parts.items() if v[1] is not None}
    health: Optional[int] = None
    if course_items:
        weight = sum(w for w, _ in active.values())
        health = int(round(sum(w * v for w, v in active.values()) / weight))
        late = [a for a in pending if a.due_date < today]
        health = int(round(clamp(health - min(OVERDUE_PENALTY_MAX, OVERDUE_PENALTY_PER_ITEM * len(late)))))

    if health is None:
        status = "no_data"
    elif health >= 80:
        status = "on_track"
    elif health >= 60:
        status = "watch"
    else:
        status = "at_risk"

    upcoming = sorted((a for a in pending if a.due_date >= today), key=lambda a: a.due_date)
    next_item = upcoming[0] if upcoming else None
    next_due = None
    if next_item:
        next_due = NextDue(
            assignment_id=next_item.id, title=next_item.title, category=next_item.category,
            due_date=next_item.due_date, days_until_due=days_until(next_item.due_date, today),
        )

    return CourseHealth(
        course_id=course.id,
        name=course.name,
        code=course.code,
        credits=course.credits,
        grade=grade,
        target_grade=course.target_grade,
        health=health,
        status=status,
        summary=_course_summary(status, grade, load, pending, next_item, today),
        trend=course_trend(course.id, snapshot.assignments),
        pending_count=len(pending),
        pending_minutes=sum(a.remaining_minutes for a in pending),
        completion_rate=completion,
        next_due=next_due,
    )


def _course_summary(
    status: str,
    grade: Optional[float],
    load: float,
    pending: List[Assignment],
    next_item: Optional[Assignment],
    today: date,
) -> str:
    """Short status line such as 'Good performance · High workload'."""
    if status == "no_data":
        return "Add assignments to start tracking"

    if any(a.due_date < today for a in pending):
        lead = "Overdue work"
    elif status == "at_risk":
        lead = "At risk"
    elif status == "watch":
        lead = "Moderate risk"
    elif grade is not None and grade >= 78:
        lead = "Strong performance" if grade >= 88 else "Good performance"
    else:
        lead = "On track"

    parts = [lead]
    if load >= 60:
        parts.append("High workload")
    if next_item and next_item.category == "exam" and days_until(next_item.due_date, today) <= 7:
        parts.append(f"Exam {describe_due(next_item.due_date, today).replace('due ', '')}")
    return " · ".join(parts)


# ── Dashboard helpers ────────────────────────────────────────────────────────

def today_overview(snapshot: StudentSnapshot, metrics: List[Metric]) -> TodayOverview:
    """The 'Today' strip on the dashboard."""
    horizon = snapshot.today + timedelta(days=6)
    remaining = [a for a in incomplete(snapshot.assignments) if a.due_date <= horizon]
    return TodayOverview(
        academic_load=next(m.level for m in metrics if m.key == "workload"),
        deadline_pressure=next(m.level for m in metrics if m.key == "deadline_pressure"),
        available_minutes_today=window_minutes_left_today(
            snapshot.now, snapshot.availability.get(snapshot.today.weekday())
        ),
        tasks_remaining=len(remaining),
        overdue_count=len(overdue(snapshot)),
    )


def build_insight(
    snapshot: StudentSnapshot,
    priorities: List[PriorityItem],
    plan_days: List[PlanDay],
) -> Insight:
    """ARWA's headline recommendation, written from the plan and priorities."""
    if not snapshot.courses:
        return Insight(message="Let's get your semester set up. Add your courses and ARWA will start tracking your recovery.")
    if not priorities:
        return Insight(message="You're all clear. No incomplete assignments right now. Add new work as it's assigned.")

    today_plan = plan_days[0] if plan_days and plan_days[0].date == snapshot.today else None
    first_study = next((b for b in today_plan.blocks if b.kind == "study"), None) if today_plan else None
    top = priorities[0]

    if first_study:
        reason = next((p.reason for p in priorities if p.assignment_id == first_study.assignment_id), top.reason)
        course = f" ({first_study.course_name})" if first_study.course_name else ""
        return Insight(
            message=(
                f"You have {format_minutes(today_plan.window_minutes)} of study time left today. "
                f"I'd start with {first_study.title}{course} at {format_clock(first_study.start)}: {lower_first(reason)}."
            ),
            action_label=f"Start {first_study.title}",
            action_assignment_id=first_study.assignment_id,
        )

    next_day = next((d for d in plan_days if d.study_minutes > 0), None)
    if next_day:
        first = next(b for b in next_day.blocks if b.kind == "study")
        when = "tomorrow" if next_day.label == "Tomorrow" else next_day.label
        return Insight(
            message=(
                f"No study time left today. Your next session is {when} at {format_clock(first.start)}, "
                f"starting with {first.title}. Top priority overall: {top.title} ({lower_first(top.reason)})."
            ),
            action_label="View plan",
            action_assignment_id=first.assignment_id,
        )
    return Insight(
        message=f"Your top priority is {top.title} ({lower_first(top.reason)}), but you have no study time set. Add your weekly availability so ARWA can plan it.",
        action_label="Set study time",
    )
