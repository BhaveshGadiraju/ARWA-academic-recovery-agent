"""Semester endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from api.auth import get_repository
from backend.services.repository import AcademicRepository
from models.schemas import SemesterCreate, SemesterResponse, SemesterUpdate

router = APIRouter(prefix="/semesters", tags=["semesters"])


def _dump(model) -> dict:
    return model.model_dump(mode="json", exclude_unset=True)


@router.get("", response_model=List[SemesterResponse])
def list_semesters(repo: AcademicRepository = Depends(get_repository)):
    """All of the caller's semesters, newest first."""
    return repo.list_semesters()


@router.post("", response_model=SemesterResponse, status_code=status.HTTP_201_CREATED)
def create_semester(body: SemesterCreate, repo: AcademicRepository = Depends(get_repository)):
    """Create a semester. A new current semester replaces the previous current one."""
    return repo.create_semester(body.model_dump(mode="json"))


@router.patch("/{semester_id}", response_model=SemesterResponse)
def update_semester(semester_id: UUID, body: SemesterUpdate, repo: AcademicRepository = Depends(get_repository)):
    """Update a semester."""
    values = _dump(body)
    if not values:
        return repo.get_semester(str(semester_id))
    return repo.update_semester(str(semester_id), values)


@router.delete("/{semester_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_semester(semester_id: UUID, repo: AcademicRepository = Depends(get_repository)):
    """Delete a semester along with its courses and assignments."""
    repo.delete_semester(str(semester_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
