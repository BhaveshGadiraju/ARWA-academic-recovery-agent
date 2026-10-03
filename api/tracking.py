"""Study session logging and wellness check-in endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status

from api.auth import get_insights, get_repository
from backend.services.errors import DataValidationError
from backend.services.insights_service import InsightsService
from backend.services.repository import AcademicRepository
from models.schemas import StudySessionCreate, StudySessionResponse, WellnessCreate, WellnessResponse

router = APIRouter(tags=["tracking"])


@router.get("/study-sessions", response_model=List[StudySessionResponse])
def list_study_sessions(repo: AcademicRepository = Depends(get_repository)):
    """Logged study sessions, newest first."""
    return repo.list_study_sessions()


@router.post("/study-sessions", response_model=StudySessionResponse, status_code=status.HTTP_201_CREATED)
def log_study_session(
    body: StudySessionCreate,
    repo: AcademicRepository = Depends(get_repository),
    insights: InsightsService = Depends(get_insights),
):
    """Log time spent on an assignment (e.g. completing a plan block)."""
    today = insights.local_now(repo.get_profile()).date()
    session_date = body.session_date or today
    if session_date > today:
        raise DataValidationError("Study sessions can't be logged in the future.")
    return repo.create_study_session({
        "assignment_id": str(body.assignment_id),
        "minutes": body.minutes,
        "session_date": session_date.isoformat(),
    })


@router.delete("/study-sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_study_session(session_id: UUID, repo: AcademicRepository = Depends(get_repository)):
    """Undo a logged session."""
    repo.delete_study_session(str(session_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/wellness", response_model=List[WellnessResponse])
def list_wellness(
    limit: int = Query(30, ge=1, le=100),
    repo: AcademicRepository = Depends(get_repository),
):
    """Recent wellness check-ins, newest first."""
    return repo.list_wellness(limit=limit)


@router.post("/wellness", response_model=WellnessResponse, status_code=status.HTTP_201_CREATED)
def create_wellness(body: WellnessCreate, repo: AcademicRepository = Depends(get_repository)):
    """Record an optional stress / sleep / energy check-in."""
    return repo.create_wellness(body.model_dump(exclude_none=True))
