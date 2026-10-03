"""
Assignment CRUD endpoints for ARWA.

Keeps the original contract (GET/POST /assignments, PUT/DELETE
/assignments/{id}, `course` as a display name) and adds course linking,
categories, grading, and completion timestamps.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from api.auth import get_repository
from backend.services.errors import DataValidationError
from backend.services.repository import AcademicRepository
from models.schemas import AssignmentCreate, AssignmentResponse, AssignmentUpdate

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _to_row(values: dict) -> dict:
    """Prepare validated values for storage."""
    if "course_id" in values and values["course_id"] is not None:
        values["course_id"] = str(values["course_id"])
        values.pop("course", None)
    if "due_date" in values and values["due_date"] is not None:
        values["due_date"] = values["due_date"].isoformat()
    return values


@router.get("", response_model=List[AssignmentResponse])
def list_assignments(
    course_id: Optional[UUID] = Query(None, description="Only assignments for this course"),
    repo: AcademicRepository = Depends(get_repository),
):
    """List the caller's assignments, sorted by due date."""
    return repo.list_assignments(course_id=str(course_id) if course_id else None)


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: UUID, repo: AcademicRepository = Depends(get_repository)):
    """One assignment."""
    return repo.get_assignment(str(assignment_id))


@router.post("", response_model=AssignmentResponse, status_code=status.HTTP_201_CREATED)
def create_assignment(assignment: AssignmentCreate, repo: AcademicRepository = Depends(get_repository)):
    """Create an assignment for the caller.

    Work created as already completed (e.g. past graded work entered during
    onboarding) gets no `completed_at`: ARWA doesn't know when it was finished,
    so it must not be counted as late or on time.
    """
    values = _to_row(assignment.model_dump(exclude_none=True))
    return repo.create_assignment(values)


@router.put("/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: UUID,
    update: AssignmentUpdate,
    repo: AcademicRepository = Depends(get_repository),
):
    """Update any subset of fields. Setting `completed` also records when it was completed."""
    values = _to_row(update.model_dump(exclude_unset=True))
    completed = values.pop("completed", None)

    if "points_earned" in values or "points_possible" in values:
        current = repo.get_assignment(str(assignment_id))
        earned = values.get("points_earned", current.get("points_earned"))
        possible = values.get("points_possible", current.get("points_possible"))
        if earned is not None and (possible is None or float(earned) > float(possible) * 1.5):
            raise DataValidationError("points_earned needs points_possible and cannot exceed 150% of it.")

    result = None
    if values:
        result = repo.update_assignment(str(assignment_id), values)
    if completed is not None:
        result = repo.set_assignment_completed(str(assignment_id), completed)
    return result or repo.get_assignment(str(assignment_id))


@router.delete("/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: UUID, repo: AcademicRepository = Depends(get_repository)):
    """Delete an assignment."""
    repo.delete_assignment(str(assignment_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
