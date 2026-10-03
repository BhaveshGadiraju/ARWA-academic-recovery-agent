"""Profile and weekly study availability endpoints."""

from typing import List

from fastapi import APIRouter, Depends

from api.auth import CurrentUser, get_current_user, get_repository
from backend.services.repository import AcademicRepository
from models.schemas import AvailabilityResponse, AvailabilityUpdate, ProfileResponse, ProfileUpdate

router = APIRouter(tags=["profile"])


def _profile_response(row: dict, user: CurrentUser) -> ProfileResponse:
    return ProfileResponse(**{**row, "email": user.email})


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    user: CurrentUser = Depends(get_current_user),
    repo: AcademicRepository = Depends(get_repository),
):
    """Return the caller's academic profile."""
    return _profile_response(repo.get_profile(), user)


@router.patch("/profile", response_model=ProfileResponse)
def update_profile(
    update: ProfileUpdate,
    user: CurrentUser = Depends(get_current_user),
    repo: AcademicRepository = Depends(get_repository),
):
    """Update profile fields (name, school, major, year, timezone, onboarding state)."""
    values = update.model_dump(exclude_unset=True)
    if not values:
        return _profile_response(repo.get_profile(), user)
    return _profile_response(repo.update_profile(values), user)


@router.get("/availability", response_model=List[AvailabilityResponse])
def get_availability(repo: AcademicRepository = Depends(get_repository)):
    """Weekly study windows (0 = Monday)."""
    return [_availability_response(r) for r in repo.list_availability()]


@router.put("/availability", response_model=List[AvailabilityResponse])
def replace_availability(update: AvailabilityUpdate, repo: AcademicRepository = Depends(get_repository)):
    """Replace the whole weekly schedule. Weekdays left out are removed."""
    days = [
        {"weekday": d.weekday, "minutes": d.minutes, "start_time": d.start_time.strftime("%H:%M")}
        for d in update.days
    ]
    return [_availability_response(r) for r in repo.replace_availability(days)]


def _availability_response(row: dict) -> AvailabilityResponse:
    return AvailabilityResponse(weekday=row["weekday"], minutes=row["minutes"], start_time=str(row["start_time"])[:5])
