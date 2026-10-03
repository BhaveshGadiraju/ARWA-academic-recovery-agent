"""Deterministic insight endpoints: dashboard, recovery plan, and progress."""

from fastapi import APIRouter, Depends, Query

from api.auth import get_insights
from backend.services.insights_service import InsightsService
from models.insights import Dashboard, Progress, RecoveryPlan

router = APIRouter(tags=["insights"])


@router.get("/dashboard", response_model=Dashboard)
def get_dashboard(insights: InsightsService = Depends(get_insights)):
    """Recovery Score, health metrics, risks, priorities, today's plan, and course health.

    Also records today's score so the trend chart has history.
    """
    return insights.dashboard()


@router.get("/plan", response_model=RecoveryPlan)
def get_plan(
    days: int = Query(7, ge=1, le=14, description="How many days to plan"),
    insights: InsightsService = Depends(get_insights),
):
    """A schedule of real assignments fitted into real study time."""
    return insights.analyze(plan_days=days).plan


@router.get("/progress", response_model=Progress)
def get_progress(insights: InsightsService = Depends(get_insights)):
    """Score history, study time, completion, missed work, and course trends."""
    return insights.progress()
