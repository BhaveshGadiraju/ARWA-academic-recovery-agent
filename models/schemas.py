"""
Request and response schemas for ARWA's REST API.

Every request body is validated here before it reaches business logic, with
limits that mirror the database constraints so users get clear 422 errors.
"""

from datetime import date, datetime, time
from typing import Annotated, Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

from models.insights import CourseHealth, Risk

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    from backports.zoneinfo import ZoneInfo  # type: ignore


def _text(max_length: int, min_length: int = 1):
    return Annotated[str, StringConstraints(strip_whitespace=True, min_length=min_length, max_length=max_length)]


Category = Literal["homework", "exam", "quiz", "project", "lab", "reading", "paper", "other"]


class StrictModel(BaseModel):
    """Reject unknown fields so typos and spoofed fields (e.g. user_id) fail loudly."""

    model_config = ConfigDict(extra="forbid")


# ── Profile & availability ───────────────────────────────────────────────────

class ProfileUpdate(StrictModel):
    full_name: Optional[_text(120)] = None
    school: Optional[_text(120)] = None
    major: Optional[_text(120)] = None
    year_in_school: Optional[_text(40)] = None
    timezone: Optional[_text(64)] = None
    onboarding_completed: Optional[bool] = None

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        try:
            ZoneInfo(value)
        except Exception as exc:
            raise ValueError("Unknown timezone") from exc
        return value


class ProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    year_in_school: Optional[str] = None
    timezone: str
    onboarding_completed: bool


class AvailabilityDay(StrictModel):
    weekday: int = Field(..., ge=0, le=6, description="0 = Monday ... 6 = Sunday")
    minutes: int = Field(..., ge=0, le=960)
    start_time: time = time(18, 0)

    @model_validator(mode="after")
    def window_fits_in_day(self) -> "AvailabilityDay":
        start = self.start_time.hour * 60 + self.start_time.minute
        if start + self.minutes > 24 * 60:
            raise ValueError("Study window must end before midnight")
        return self


class AvailabilityUpdate(StrictModel):
    days: List[AvailabilityDay] = Field(..., max_length=7)

    @field_validator("days")
    @classmethod
    def unique_weekdays(cls, days: List[AvailabilityDay]) -> List[AvailabilityDay]:
        if len({d.weekday for d in days}) != len(days):
            raise ValueError("Each weekday can appear only once")
        return days


class AvailabilityResponse(BaseModel):
    weekday: int
    minutes: int
    start_time: str


# ── Semesters ────────────────────────────────────────────────────────────────

class SemesterCreate(StrictModel):
    name: _text(80)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = True

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class SemesterUpdate(StrictModel):
    name: Optional[_text(80)] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date must be on or after start_date")
        return self


class SemesterResponse(BaseModel):
    id: str
    name: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool
    created_at: datetime


# ── Courses ──────────────────────────────────────────────────────────────────

class CourseCreate(StrictModel):
    name: _text(120)
    code: Optional[_text(30)] = None
    credits: float = Field(3.0, gt=0, le=12)
    target_grade: Optional[float] = Field(None, ge=0, le=100)
    semester_id: Optional[UUID] = Field(None, description="Defaults to the current semester")


class CourseUpdate(StrictModel):
    name: Optional[_text(120)] = None
    code: Optional[_text(30, min_length=0)] = None
    credits: Optional[float] = Field(None, gt=0, le=12)
    target_grade: Optional[float] = Field(None, ge=0, le=100)
    semester_id: Optional[UUID] = None


class CourseResponse(BaseModel):
    id: str
    semester_id: str
    name: str
    code: Optional[str] = None
    credits: float
    target_grade: Optional[float] = None
    created_at: datetime


# ── Assignments ──────────────────────────────────────────────────────────────

class _AssignmentFields(StrictModel):
    """Shared validation for assignment create/update."""

    @model_validator(mode="after")
    def points_are_consistent(self):
        earned = getattr(self, "points_earned", None)
        possible = getattr(self, "points_possible", None)
        if earned is not None and possible is not None and earned > possible * 1.5:
            raise ValueError("points_earned cannot exceed 150% of points_possible")
        return self


class AssignmentCreate(_AssignmentFields):
    title: _text(200)
    course_id: Optional[UUID] = None
    course: Optional[_text(120)] = Field(None, description="Legacy free-text course name; prefer course_id")
    category: Category = "homework"
    difficulty: float = Field(0.5, ge=0, le=1)
    estimated_hours: float = Field(..., ge=0, le=200)
    due_date: date
    completed: bool = False
    points_possible: Optional[float] = Field(None, gt=0, le=10000)
    points_earned: Optional[float] = Field(None, ge=0, le=15000)
    notes: Optional[_text(2000, min_length=0)] = None

    @model_validator(mode="after")
    def needs_course_and_points(self):
        if self.course_id is None and not self.course:
            raise ValueError("Provide course_id (or a course name)")
        if self.points_earned is not None and self.points_possible is None:
            raise ValueError("points_possible is required when points_earned is set")
        return self


class AssignmentUpdate(_AssignmentFields):
    title: Optional[_text(200)] = None
    course_id: Optional[UUID] = None
    course: Optional[_text(120)] = None
    category: Optional[Category] = None
    difficulty: Optional[float] = Field(None, ge=0, le=1)
    estimated_hours: Optional[float] = Field(None, ge=0, le=200)
    due_date: Optional[date] = None
    completed: Optional[bool] = None
    points_possible: Optional[float] = Field(None, gt=0, le=10000)
    points_earned: Optional[float] = Field(None, ge=0, le=15000)
    notes: Optional[_text(2000, min_length=0)] = None


class AssignmentResponse(BaseModel):
    """Backwards compatible with the original contract, plus MVP fields."""

    id: str
    title: str
    course: Optional[str] = None
    difficulty: float
    estimated_hours: float
    due_date: str
    completed: bool
    created_at: str
    updated_at: str
    course_id: Optional[str] = None
    course_code: Optional[str] = None
    category: str = "homework"
    points_possible: Optional[float] = None
    points_earned: Optional[float] = None
    completed_at: Optional[str] = None
    notes: Optional[str] = None


# ── Study sessions & wellness ────────────────────────────────────────────────

class StudySessionCreate(StrictModel):
    assignment_id: UUID
    minutes: int = Field(..., ge=1, le=720)
    session_date: Optional[date] = Field(None, description="Defaults to today in the student's timezone")


class StudySessionResponse(BaseModel):
    id: str
    assignment_id: str
    minutes: int
    session_date: date
    created_at: datetime


class WellnessCreate(StrictModel):
    stress_level: int = Field(..., ge=1, le=10)
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    energy_level: Optional[int] = Field(None, ge=1, le=5)
    note: Optional[_text(500, min_length=0)] = None


class WellnessResponse(BaseModel):
    id: str
    stress_level: int
    sleep_hours: Optional[float] = None
    energy_level: Optional[int] = None
    note: Optional[str] = None
    created_at: datetime


# ── Course detail ────────────────────────────────────────────────────────────

class CourseDetailResponse(BaseModel):
    course: CourseResponse
    health: CourseHealth
    assignments: List[AssignmentResponse]
    risks: List[Risk]
    recommended_action: str


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(StrictModel):
    message: _text(2000)


class ChatMessageResponse(BaseModel):
    id: str
    role: Literal["user", "assistant"]
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ChatReplyResponse(BaseModel):
    message: ChatMessageResponse
    tools_used: List[str]
    ai_powered: bool
