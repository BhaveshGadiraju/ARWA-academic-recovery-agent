"""
ARWA data layer.

All database access goes through AcademicRepository. It uses a Supabase client
authenticated with the student's own JWT, so Postgres Row Level Security
enforces ownership on every query. Queries also filter by user_id explicitly
as defence in depth; the user_id always comes from the verified token, never
from the request body.
"""

import logging
import re
from datetime import date, datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from postgrest.exceptions import APIError
from supabase import Client

from backend.services.errors import ConflictError, DataValidationError, NotFoundError

logger = logging.getLogger(__name__)

Row = Dict[str, Any]

ASSIGNMENT_SELECT = "*, courses(name, code)"

_VALIDATION_CODES = {"23514", "23502", "22P02", "22001", "22003", "22007", "22008", "23503"}


def _run(query: Callable[[], Any]) -> List[Row]:
    """Execute a PostgREST query and translate database errors into domain errors."""
    try:
        response = query()
    except APIError as exc:
        code = getattr(exc, "code", None)
        logger.info("Database rejected query: code=%s message=%s", code, getattr(exc, "message", ""))
        if code in _VALIDATION_CODES:
            raise DataValidationError("Some values were not accepted. Check the fields and try again.") from exc
        if code == "23505":
            raise ConflictError("That record already exists.") from exc
        if code in ("42501", "PGRST116"):
            raise NotFoundError("Not found.") from exc
        raise
    data = response.data if response is not None else None
    if data is None:
        return []
    return data if isinstance(data, list) else [data]


def _first(rows: List[Row], what: str) -> Row:
    """Return the first row or raise NotFoundError."""
    if not rows:
        raise NotFoundError(f"{what} not found.")
    return rows[0]


def normalize_assignment(row: Row) -> Row:
    """Flatten the embedded course so `course` is always the display name."""
    row = dict(row)
    course = row.pop("courses", None)
    if course:
        row["course"] = course.get("name") or row.get("course")
        row["course_code"] = course.get("code")
    else:
        row.setdefault("course_code", None)
    return row


class AcademicRepository:
    """User-scoped CRUD over the student's academic data."""

    def __init__(self, client: Client, user_id: str):
        self.client = client
        self.user_id = user_id

    def _table(self, name: str):
        return self.client.table(name)

    # ── Profile ──────────────────────────────────────────────────────────────

    def get_profile(self) -> Row:
        """Return the profile row, creating it if the signup trigger has not."""
        rows = _run(lambda: self._table("profiles").select("*").eq("id", self.user_id).execute())
        if rows:
            return rows[0]
        return _first(_run(lambda: self._table("profiles").insert({"id": self.user_id}).execute()), "Profile")

    def update_profile(self, values: Row) -> Row:
        """Update profile fields."""
        self.get_profile()
        rows = _run(lambda: self._table("profiles").update(values).eq("id", self.user_id).execute())
        return _first(rows, "Profile")

    # ── Availability ─────────────────────────────────────────────────────────

    def list_availability(self) -> List[Row]:
        """Weekly study windows, Monday first."""
        return _run(lambda: self._table("study_availability").select("*")
                    .eq("user_id", self.user_id).order("weekday").execute())

    def replace_availability(self, days: List[Row]) -> List[Row]:
        """Upsert the given weekdays and remove any weekday not provided."""
        rows = [{**d, "user_id": self.user_id} for d in days]
        if rows:
            _run(lambda: self._table("study_availability").upsert(rows, on_conflict="user_id,weekday").execute())
        keep = [d["weekday"] for d in days]
        delete = self._table("study_availability").delete().eq("user_id", self.user_id)
        if keep:
            delete = delete.not_.in_("weekday", keep)
        _run(lambda: delete.execute())
        return self.list_availability()

    # ── Semesters ────────────────────────────────────────────────────────────

    def list_semesters(self) -> List[Row]:
        """All semesters, newest first."""
        return _run(lambda: self._table("semesters").select("*")
                    .eq("user_id", self.user_id).order("created_at", desc=True).execute())

    def current_semester(self) -> Optional[Row]:
        """The semester marked current, if any."""
        rows = _run(lambda: self._table("semesters").select("*")
                    .eq("user_id", self.user_id).eq("is_current", True).limit(1).execute())
        return rows[0] if rows else None

    def get_semester(self, semester_id: str) -> Row:
        """One semester by id."""
        rows = _run(lambda: self._table("semesters").select("*")
                    .eq("user_id", self.user_id).eq("id", semester_id).execute())
        return _first(rows, "Semester")

    def create_semester(self, values: Row) -> Row:
        """Create a semester; a new current semester replaces the previous current one."""
        if values.get("is_current", True):
            self._clear_current_semester()
        rows = _run(lambda: self._table("semesters").insert({**values, "user_id": self.user_id}).execute())
        return _first(rows, "Semester")

    def update_semester(self, semester_id: str, values: Row) -> Row:
        """Update a semester."""
        self.get_semester(semester_id)
        if values.get("is_current"):
            self._clear_current_semester(exclude_id=semester_id)
        rows = _run(lambda: self._table("semesters").update(values)
                    .eq("user_id", self.user_id).eq("id", semester_id).execute())
        return _first(rows, "Semester")

    def delete_semester(self, semester_id: str) -> None:
        """Delete a semester and (via cascade) its courses and assignments."""
        self.get_semester(semester_id)
        _run(lambda: self._table("semesters").delete().eq("user_id", self.user_id).eq("id", semester_id).execute())

    def _clear_current_semester(self, exclude_id: Optional[str] = None) -> None:
        query = self._table("semesters").update({"is_current": False}).eq("user_id", self.user_id).eq("is_current", True)
        if exclude_id:
            query = query.neq("id", exclude_id)
        _run(lambda: query.execute())

    # ── Courses ──────────────────────────────────────────────────────────────

    def list_courses(self, semester_id: Optional[str] = None) -> List[Row]:
        """Courses, optionally limited to one semester."""
        query = self._table("courses").select("*").eq("user_id", self.user_id)
        if semester_id:
            query = query.eq("semester_id", semester_id)
        return _run(lambda: query.order("created_at").execute())

    def get_course(self, course_id: str) -> Row:
        """One course by id."""
        rows = _run(lambda: self._table("courses").select("*")
                    .eq("user_id", self.user_id).eq("id", course_id).execute())
        return _first(rows, "Course")

    def create_course(self, values: Row) -> Row:
        """Create a course in one of the student's semesters."""
        self.get_semester(values["semester_id"])
        rows = _run(lambda: self._table("courses").insert({**values, "user_id": self.user_id}).execute())
        return _first(rows, "Course")

    def update_course(self, course_id: str, values: Row) -> Row:
        """Update a course."""
        self.get_course(course_id)
        if "semester_id" in values:
            self.get_semester(values["semester_id"])
        rows = _run(lambda: self._table("courses").update(values)
                    .eq("user_id", self.user_id).eq("id", course_id).execute())
        return _first(rows, "Course")

    def delete_course(self, course_id: str) -> None:
        """Delete a course and its assignments."""
        self.get_course(course_id)
        _run(lambda: self._table("courses").delete().eq("user_id", self.user_id).eq("id", course_id).execute())

    # ── Assignments ──────────────────────────────────────────────────────────

    def list_assignments(self, course_id: Optional[str] = None) -> List[Row]:
        """Assignments sorted by due date, with course names attached."""
        query = self._table("assignments").select(ASSIGNMENT_SELECT).eq("user_id", self.user_id)
        if course_id:
            query = query.eq("course_id", course_id)
        rows = _run(lambda: query.order("due_date").execute())
        return [normalize_assignment(r) for r in rows]

    def get_assignment(self, assignment_id: str) -> Row:
        """One assignment by id."""
        rows = _run(lambda: self._table("assignments").select(ASSIGNMENT_SELECT)
                    .eq("user_id", self.user_id).eq("id", assignment_id).execute())
        return normalize_assignment(_first(rows, "Assignment"))

    def create_assignment(self, values: Row) -> Row:
        """Create an assignment, optionally linked to one of the student's courses."""
        if values.get("course_id"):
            self.get_course(values["course_id"])
        rows = _run(lambda: self._table("assignments").insert({**values, "user_id": self.user_id}).execute())
        return self.get_assignment(_first(rows, "Assignment")["id"])

    def update_assignment(self, assignment_id: str, values: Row) -> Row:
        """Update an assignment."""
        self.get_assignment(assignment_id)
        if values.get("course_id"):
            self.get_course(values["course_id"])
        _run(lambda: self._table("assignments").update(values)
             .eq("user_id", self.user_id).eq("id", assignment_id).execute())
        return self.get_assignment(assignment_id)

    def set_assignment_completed(self, assignment_id: str, completed: bool) -> Row:
        """Mark an assignment complete (stamping completed_at) or incomplete."""
        completed_at = datetime.now(timezone.utc).isoformat() if completed else None
        return self.update_assignment(assignment_id, {"completed": completed, "completed_at": completed_at})

    def delete_assignment(self, assignment_id: str) -> None:
        """Delete an assignment."""
        self.get_assignment(assignment_id)
        _run(lambda: self._table("assignments").delete().eq("user_id", self.user_id).eq("id", assignment_id).execute())

    # ── Study sessions ───────────────────────────────────────────────────────

    def list_study_sessions(self, since: Optional[date] = None) -> List[Row]:
        """Logged study sessions, newest first."""
        query = self._table("study_sessions").select("*").eq("user_id", self.user_id)
        if since:
            query = query.gte("session_date", since.isoformat())
        return _run(lambda: query.order("session_date", desc=True).execute())

    def create_study_session(self, values: Row) -> Row:
        """Log study time on one of the student's assignments."""
        self.get_assignment(values["assignment_id"])
        rows = _run(lambda: self._table("study_sessions").insert({**values, "user_id": self.user_id}).execute())
        return _first(rows, "Study session")

    def delete_study_session(self, session_id: str) -> None:
        """Remove a logged session."""
        rows = _run(lambda: self._table("study_sessions").select("id")
                    .eq("user_id", self.user_id).eq("id", session_id).execute())
        _first(rows, "Study session")
        _run(lambda: self._table("study_sessions").delete().eq("user_id", self.user_id).eq("id", session_id).execute())

    # ── Wellness ─────────────────────────────────────────────────────────────

    def list_wellness(self, limit: int = 30) -> List[Row]:
        """Recent wellness check-ins, newest first."""
        return _run(lambda: self._table("wellness_checkins").select("*")
                    .eq("user_id", self.user_id).order("created_at", desc=True).limit(limit).execute())

    def create_wellness(self, values: Row) -> Row:
        """Record a wellness check-in."""
        rows = _run(lambda: self._table("wellness_checkins").insert({**values, "user_id": self.user_id}).execute())
        return _first(rows, "Wellness check-in")

    # ── Recovery snapshots ───────────────────────────────────────────────────

    def list_snapshots(self, since: Optional[date] = None) -> List[Row]:
        """Daily Recovery Score history, oldest first."""
        query = self._table("recovery_snapshots").select("snapshot_date, score, metrics, factors").eq("user_id", self.user_id)
        if since:
            query = query.gte("snapshot_date", since.isoformat())
        return _run(lambda: query.order("snapshot_date").execute())

    def upsert_snapshot(self, snapshot_date: date, score: int, metrics: Row, factors: List[Row]) -> None:
        """Store today's score; recalculations on the same day overwrite it."""
        row = {
            "user_id": self.user_id,
            "snapshot_date": snapshot_date.isoformat(),
            "score": score,
            "metrics": metrics,
            "factors": factors,
        }
        _run(lambda: self._table("recovery_snapshots").upsert(row, on_conflict="user_id,snapshot_date").execute())

    # ── Chat ─────────────────────────────────────────────────────────────────

    def list_chat_messages(self, limit: int = 50) -> List[Row]:
        """Most recent chat messages, returned oldest first."""
        rows = _run(lambda: self._table("chat_messages").select("id, role, content, metadata, created_at")
                    .eq("user_id", self.user_id).order("created_at", desc=True).limit(limit).execute())
        return list(reversed(rows))

    def add_chat_message(self, role: str, content: str, metadata: Optional[Row] = None) -> Row:
        """Append a message to the conversation."""
        row = {"user_id": self.user_id, "role": role, "content": content, "metadata": metadata or {}}
        return _first(_run(lambda: self._table("chat_messages").insert(row).execute()), "Message")

    def clear_chat(self) -> None:
        """Delete the whole conversation."""
        _run(lambda: self._table("chat_messages").delete().eq("user_id", self.user_id).execute())


_FRACTION = re.compile(r"\.(\d+)")


def parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    """Parse a PostgREST timestamp string.

    Postgres trims trailing zeros from fractional seconds, which Python 3.9's
    fromisoformat rejects, so the fraction is padded to microseconds first.
    """
    if not value:
        return None
    text = value.replace("Z", "+00:00")
    text = _FRACTION.sub(lambda m: "." + m.group(1)[:6].ljust(6, "0"), text, count=1)
    return datetime.fromisoformat(text)
