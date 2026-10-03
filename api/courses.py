"""Course endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status

from api.auth import get_insights, get_repository
from backend.services.errors import ConflictError
from backend.services.insights_service import InsightsService
from backend.services.repository import AcademicRepository
from models.insights import CourseHealth
from models.schemas import CourseCreate, CourseDetailResponse, CourseResponse, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[CourseResponse])
def list_courses(repo: AcademicRepository = Depends(get_repository)):
    """Courses in the current semester."""
    semester = repo.current_semester()
    return repo.list_courses(semester["id"]) if semester else []


@router.get("/health", response_model=List[CourseHealth])
def list_course_health(insights: InsightsService = Depends(get_insights)):
    """Health status for every course in the current semester."""
    return insights.course_health_list()


@router.post("", response_model=CourseResponse, status_code=status.HTTP_201_CREATED)
def create_course(body: CourseCreate, repo: AcademicRepository = Depends(get_repository)):
    """Add a course to the given semester (or the current one)."""
    values = body.model_dump(mode="json", exclude_none=True)
    if "semester_id" not in values:
        semester = repo.current_semester()
        if semester is None:
            raise ConflictError("Create a semester before adding courses.")
        values["semester_id"] = semester["id"]
    return repo.create_course(values)


@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course(course_id: UUID, insights: InsightsService = Depends(get_insights)):
    """Course page: grade, health, assignments, risks, and the recommended next step."""
    return insights.course_detail(str(course_id))


@router.patch("/{course_id}", response_model=CourseResponse)
def update_course(course_id: UUID, body: CourseUpdate, repo: AcademicRepository = Depends(get_repository)):
    """Update a course."""
    values = body.model_dump(mode="json", exclude_unset=True)
    if "code" in values and values["code"] == "":
        values["code"] = None
    if not values:
        return repo.get_course(str(course_id))
    return repo.update_course(str(course_id), values)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: UUID, repo: AcademicRepository = Depends(get_repository)):
    """Delete a course and its assignments."""
    repo.delete_course(str(course_id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
