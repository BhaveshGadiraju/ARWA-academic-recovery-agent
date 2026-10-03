"""
Domain types for ARWA's deterministic academic engine.

These are plain, immutable snapshots of a student's data at a moment in time.
The engine and planner are pure functions over these types, which keeps every
calculation reproducible and unit-testable without a database.
"""

from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import Dict, List, Optional

# A started-but-unfinished assignment always keeps at least this much work in
# the plan, so logging study time never makes incomplete work disappear.
MIN_WRAP_UP_MINUTES = 15


@dataclass(frozen=True)
class Course:
    """A course in the student's current semester."""

    id: str
    name: str
    code: Optional[str] = None
    credits: float = 3.0
    target_grade: Optional[float] = None

    @property
    def display_name(self) -> str:
        """Short label used in UI copy and AI answers."""
        return self.code or self.name


@dataclass(frozen=True)
class Assignment:
    """An assignment or exam, with grading and progress information."""

    id: str
    title: str
    due_date: date
    estimated_minutes: int
    category: str = "homework"
    course_id: Optional[str] = None
    course_name: Optional[str] = None
    completed: bool = False
    completed_at: Optional[datetime] = None
    points_possible: Optional[float] = None
    points_earned: Optional[float] = None
    logged_minutes: int = 0

    @property
    def is_graded(self) -> bool:
        """True when both earned and possible points are recorded."""
        return self.points_earned is not None and bool(self.points_possible)

    @property
    def grade_percent(self) -> Optional[float]:
        """Score on this assignment as a percentage, if graded."""
        if not self.is_graded:
            return None
        return 100.0 * float(self.points_earned) / float(self.points_possible)

    @property
    def remaining_minutes(self) -> int:
        """Estimated work left, after subtracting logged study sessions."""
        if self.completed or self.estimated_minutes <= 0:
            return 0
        left = self.estimated_minutes - self.logged_minutes
        return max(left, MIN_WRAP_UP_MINUTES)


@dataclass(frozen=True)
class DayAvailability:
    """Study window for one weekday (0 = Monday ... 6 = Sunday)."""

    weekday: int
    minutes: int
    start_time: time = time(18, 0)


@dataclass(frozen=True)
class Wellness:
    """Most recent optional wellness check-in."""

    stress_level: int
    sleep_hours: Optional[float] = None
    energy_level: Optional[int] = None
    created_at: Optional[datetime] = None


@dataclass(frozen=True)
class StudentSnapshot:
    """Everything the engine needs, captured in the student's local time."""

    now: datetime
    courses: List[Course] = field(default_factory=list)
    assignments: List[Assignment] = field(default_factory=list)
    availability: Dict[int, DayAvailability] = field(default_factory=dict)
    wellness: Optional[Wellness] = None

    @property
    def today(self) -> date:
        """The student's local calendar date."""
        return self.now.date()

    def course(self, course_id: Optional[str]) -> Optional[Course]:
        """Look up a course by id."""
        return next((c for c in self.courses if c.id == course_id), None)
