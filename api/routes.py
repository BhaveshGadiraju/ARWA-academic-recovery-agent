"""Top-level router: health checks, the legacy /analyze endpoint, and all resource routers."""

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.analyses import router as analyses_router
from api.assignments import router as assignments_router
from api.auth import CurrentUser, get_current_user_optional
from api.chat import router as chat_router
from api.controller import RecoveryController
from api.courses import router as courses_router
from api.insights import router as insights_router
from api.profile import router as profile_router
from api.semesters import router as semesters_router
from api.tracking import router as tracking_router
from backend.services.persistence import persist_analysis
from models.api_models import StudentRequest

logger = logging.getLogger(__name__)

router = APIRouter()
controller = RecoveryController()


@router.get("/")
def home():
    """Service banner."""
    return {
        "message": "ARWA AI Backend",
        "status": "running",
        "version": "3.0.0",
        "ai_engine": "Groq tool-calling agent with deterministic recovery engine",
    }


@router.get("/health")
def health():
    """Liveness plus which integrations are configured (never their values)."""
    return {
        "status": "healthy",
        "agent": "ARWA Analysis Service",
        "ai_available": bool(os.environ.get("GROQ_API_KEY")),
        "database_available": bool(os.environ.get("SUPABASE_URL")),
        "model": os.environ.get("GROQ_MODEL", "not configured"),
    }


@router.post("/analyze")
async def analyze(
    student: StudentRequest,
    user: Optional[CurrentUser] = Depends(get_current_user_optional),
):
    """Legacy one-shot analysis. Persists results when the user is authenticated."""
    try:
        result = await controller.analyze(student)
    except (KeyError, ValueError) as exc:
        logger.warning("Invalid /analyze request: %s", exc)
        raise HTTPException(status_code=400, detail="The submitted data could not be analyzed.")

    if user:
        analysis_id = await persist_analysis(
            user_id=user.id,
            access_token=user.access_token,
            student_data=student.model_dump(),
            result=result,
        )
        if analysis_id:
            result["analysis_id"] = analysis_id
    return result


for resource_router in (
    profile_router,
    semesters_router,
    courses_router,
    assignments_router,
    tracking_router,
    insights_router,
    chat_router,
    analyses_router,
):
    router.include_router(resource_router)
