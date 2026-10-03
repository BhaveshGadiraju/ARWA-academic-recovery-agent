"""
Authentication dependencies for ARWA.

Every protected route depends on `get_current_user` (or `get_repository`),
which verifies the Bearer token with Supabase. The user id used for all data
access comes from the verified token, never from the request body.
"""

from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.services.insights_service import InsightsService
from backend.services.repository import AcademicRepository
from backend.services.supabase_client import get_user_client, verify_token

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """The authenticated caller."""

    id: str
    email: Optional[str]
    access_token: str


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> CurrentUser:
    """Verify the Bearer token. Raises 401 if it is missing, invalid, or expired."""
    if credentials is None:
        raise _unauthorized("Authentication required")
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise _unauthorized("Invalid or expired token")
    return CurrentUser(id=payload["id"], email=payload.get("email"), access_token=credentials.credentials)


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer),
) -> Optional[CurrentUser]:
    """Like get_current_user, but returns None instead of raising."""
    if credentials is None:
        return None
    payload = verify_token(credentials.credentials)
    if payload is None:
        return None
    return CurrentUser(id=payload["id"], email=payload.get("email"), access_token=credentials.credentials)


def get_repository(user: CurrentUser = Depends(get_current_user)) -> AcademicRepository:
    """A repository bound to the caller's identity and RLS-scoped client."""
    return AcademicRepository(get_user_client(user.access_token), user.id)


def get_insights(repo: AcademicRepository = Depends(get_repository)) -> InsightsService:
    """Business-logic service for the caller."""
    return InsightsService(repo)
