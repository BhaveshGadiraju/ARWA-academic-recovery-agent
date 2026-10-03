"""
Analysis History API endpoints for ARWA (legacy /analyze results).

Provides read-only access to persisted analysis history.
All operations are scoped to the authenticated user via RLS.
"""

from typing import Any, Dict, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import CurrentUser, get_current_user
from backend.services.supabase_client import get_user_client

router = APIRouter(prefix="/analyses", tags=["analyses"])


class AnalysisSummaryResponse(BaseModel):
    analysis_id: str
    created_at: str
    academic_risk: int
    academic_risk_level: str
    burnout_risk: int
    burnout_risk_level: str
    recovery_score: int


class AnalysisDetailResponse(BaseModel):
    analysis: Dict[str, Any]
    analysis_assignments: List[Dict[str, Any]]
    risk_factors: List[Dict[str, Any]]
    priorities: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]
    recovery_plan_days: List[Dict[str, Any]]
    recovery_plan_tasks: List[Dict[str, Any]]
    explanations: List[Dict[str, Any]]


@router.get("", response_model=List[AnalysisSummaryResponse])
def list_analyses(user: CurrentUser = Depends(get_current_user)):
    """List the authenticated user's analyses, newest first."""
    client = get_user_client(user.access_token)
    response = (
        client.table("analyses")
        .select(
            "id, created_at, academic_risk_score, academic_risk_level, "
            "burnout_risk_score, burnout_risk_level, recovery_score_value"
        )
        .order("created_at", desc=True)
        .execute()
    )
    return [
        {
            "analysis_id": row["id"],
            "created_at": row["created_at"],
            "academic_risk": row["academic_risk_score"],
            "academic_risk_level": row["academic_risk_level"],
            "burnout_risk": row["burnout_risk_score"],
            "burnout_risk_level": row["burnout_risk_level"],
            "recovery_score": row["recovery_score_value"],
        }
        for row in response.data
    ]


@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
def get_analysis(analysis_id: UUID, user: CurrentUser = Depends(get_current_user)):
    """Return the complete persisted analysis for the authenticated user.

    RLS ensures only the owner can fetch their analysis; fetching another
    user's analysis returns no rows, which maps to a 404.
    """
    client = get_user_client(user.access_token)
    analysis_key = str(analysis_id)

    def _fetch(table: str, column: str, value: str) -> List[Dict[str, Any]]:
        return list(client.table(table).select("*").eq(column, value).execute().data)

    rows = _fetch("analyses", "id", analysis_key)
    if not rows:
        raise HTTPException(status_code=404, detail="Analysis not found")
    analysis = dict(rows[0])
    analysis.pop("user_id", None)

    recovery_plan_days = _fetch("recovery_plan_days", "analysis_id", analysis_key)
    recovery_plan_tasks: List[Dict[str, Any]] = []
    for day in recovery_plan_days:
        day["tasks"] = _fetch("recovery_plan_tasks", "plan_day_id", day["id"])
        recovery_plan_tasks.extend(day["tasks"])

    return {
        "analysis": analysis,
        "analysis_assignments": _fetch("analysis_assignments", "analysis_id", analysis_key),
        "risk_factors": _fetch("risk_factors", "analysis_id", analysis_key),
        "priorities": _fetch("priorities", "analysis_id", analysis_key),
        "recommendations": _fetch("recommendations", "analysis_id", analysis_key),
        "recovery_plan_days": recovery_plan_days,
        "recovery_plan_tasks": recovery_plan_tasks,
        "explanations": _fetch("explanations", "analysis_id", analysis_key),
    }
