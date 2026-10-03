"""
Output models for ARWA's deterministic insights.

The engine builds these directly and the API returns them as typed responses,
so there is a single definition of every score, metric, risk, and plan shape.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["critical", "high", "moderate", "low"]
Impact = Literal["positive", "negative", "neutral"]


class ScoreFactor(BaseModel):
    """One transparent input to the Recovery Score."""

    key: str
    label: str
    detail: str
    impact: Impact
    value: Optional[int] = Field(None, description="Component value 0-100; null when there is no data")
    weight: float = Field(..., description="Share of the score this component controls (0-1)")
    points_lost: int = Field(..., description="Score points this factor is costing the student")


class RecoveryScore(BaseModel):
    """ARWA's Recovery Score: a planning metric, not a validated measure."""

    score: Optional[int] = None
    band: Literal["on_track", "manageable", "under_pressure", "needs_recovery", "not_enough_data"]
    band_label: str
    headline: str
    factors: List[ScoreFactor]
    previous_score: Optional[int] = None
    delta: Optional[int] = None


class Metric(BaseModel):
    """An academic health metric with a defined meaning."""

    key: Literal["workload", "deadline_pressure", "performance", "capacity"]
    label: str
    value: Optional[int] = None
    level: str
    summary: str
    meaning: str
    higher_is_better: bool


class Risk(BaseModel):
    """A deterministic academic risk with supporting data and a next step."""

    id: str
    severity: Severity
    kind: str
    title: str
    reason: str
    action: str
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    assignment_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)


class PriorityItem(BaseModel):
    """An incomplete assignment ranked by what to do next."""

    rank: int
    assignment_id: str
    title: str
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    category: str
    due_date: date
    days_until_due: int
    remaining_minutes: int
    score: float
    reason: str


class PlanBlock(BaseModel):
    """A scheduled study block or break."""

    kind: Literal["study", "break"]
    start: str
    end: str
    minutes: int
    assignment_id: Optional[str] = None
    title: Optional[str] = None
    course_name: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[date] = None


class PlanDay(BaseModel):
    """One day of the recovery plan."""

    date: date
    label: str
    window_minutes: int
    study_minutes: int
    blocks: List[PlanBlock]


class UnscheduledWork(BaseModel):
    """Work that does not fit into available time before its deadline."""

    assignment_id: str
    title: str
    course_name: Optional[str] = None
    due_date: date
    unscheduled_minutes: int


class RecoveryPlan(BaseModel):
    """A schedule built only from the student's real assignments and time."""

    generated_at: datetime
    days: List[PlanDay]
    unscheduled: List[UnscheduledWork]
    required_minutes: int
    planned_minutes: int
    is_feasible: bool


class NextDue(BaseModel):
    """The next incomplete item in a course."""

    assignment_id: str
    title: str
    category: str
    due_date: date
    days_until_due: int


class CourseHealth(BaseModel):
    """Per-course status for the courses list and course page."""

    course_id: str
    name: str
    code: Optional[str] = None
    credits: float
    grade: Optional[float] = None
    target_grade: Optional[float] = None
    health: Optional[int] = None
    status: Literal["on_track", "watch", "at_risk", "no_data"]
    summary: str
    trend: Optional[float] = Field(None, description="Recent graded work minus earlier graded work, in points")
    pending_count: int
    pending_minutes: int
    completion_rate: Optional[int] = None
    next_due: Optional[NextDue] = None


class TodayOverview(BaseModel):
    """At-a-glance daily status."""

    academic_load: str
    deadline_pressure: str
    available_minutes_today: int
    tasks_remaining: int
    overdue_count: int


class Insight(BaseModel):
    """ARWA's deterministic headline recommendation for the dashboard."""

    message: str
    action_label: Optional[str] = None
    action_assignment_id: Optional[str] = None


class TrendPoint(BaseModel):
    """One day of Recovery Score history."""

    date: date
    score: int


class SetupStatus(BaseModel):
    """What the student still needs to add for a full analysis."""

    onboarding_completed: bool
    has_courses: bool
    has_assignments: bool
    has_availability: bool
    has_grades: bool


class Dashboard(BaseModel):
    """Everything the home screen needs in one response."""

    generated_at: datetime
    setup: SetupStatus
    score: RecoveryScore
    metrics: List[Metric]
    today: TodayOverview
    risks: List[Risk]
    priorities: List[PriorityItem]
    plan_today: Optional[PlanDay] = None
    insight: Insight
    courses: List[CourseHealth]
    trend: List[TrendPoint]


class StudyDay(BaseModel):
    """Study minutes logged on a day versus minutes planned that day."""

    date: date
    studied_minutes: int
    planned_minutes: Optional[int] = None


class WeeklyCompletion(BaseModel):
    """Assignments completed in a calendar week (starting Monday)."""

    week_start: date
    completed: int
    on_time: int


class MissedItem(BaseModel):
    """Overdue or late work."""

    assignment_id: str
    title: str
    course_name: Optional[str] = None
    due_date: date
    status: Literal["overdue", "late"]


class CourseTrend(BaseModel):
    """Running course grade after each graded assignment."""

    course_id: str
    name: str
    points: List[Dict[str, Any]]


class Progress(BaseModel):
    """History and trends for the Progress screen."""

    score_history: List[TrendPoint]
    study_days: List[StudyDay]
    weekly_completion: List[WeeklyCompletion]
    missed: List[MissedItem]
    course_trends: List[CourseTrend]
    totals: Dict[str, int]
