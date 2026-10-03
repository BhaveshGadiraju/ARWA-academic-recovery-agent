"""
Supabase Client Service for ARWA.

Provides user-scoped Supabase clients (Row Level Security applies via the
user's JWT) and access-token verification. The backend never needs the
service-role key at runtime.
"""

import hashlib
import logging
import os
import threading
import time
from typing import Dict, Optional, Tuple

from supabase import Client, create_client

from backend.services.errors import ServiceUnavailableError

logger = logging.getLogger(__name__)

TOKEN_CACHE_SECONDS = 60
_token_cache: Dict[str, Tuple[float, dict]] = {}
_token_cache_lock = threading.Lock()


def _config() -> Tuple[str, str]:
    url = os.environ.get("SUPABASE_URL")
    anon_key = os.environ.get("SUPABASE_ANON_KEY")
    if not url or not anon_key:
        raise ServiceUnavailableError("The database is not configured.")
    return url, anon_key


def get_user_client(access_token: str) -> Client:
    """Return a Supabase client scoped to a specific user via JWT token.

    This client respects Row Level Security policies.
    """
    url, anon_key = _config()
    client = create_client(url, anon_key)
    client.postgrest.auth(access_token)
    return client


def verify_token(access_token: str) -> Optional[dict]:
    """Verify a Supabase access token and return {'id', 'email'}, or None if invalid.

    Verification asks Supabase Auth (so revoked sessions are rejected). Valid
    results are cached briefly, keyed by a hash of the token.
    """
    if not access_token:
        return None
    key = hashlib.sha256(access_token.encode()).hexdigest()
    now = time.monotonic()
    with _token_cache_lock:
        cached = _token_cache.get(key)
        if cached and cached[0] > now:
            return cached[1]

    try:
        url, anon_key = _config()
        user_response = create_client(url, anon_key).auth.get_user(access_token)
    except ServiceUnavailableError:
        raise
    except Exception as exc:
        logger.info("Token verification failed: %s", type(exc).__name__)
        return None

    if not user_response or not user_response.user:
        return None
    payload = {"id": user_response.user.id, "email": user_response.user.email}
    with _token_cache_lock:
        if len(_token_cache) > 5000:
            _token_cache.clear()
        _token_cache[key] = (now + TOKEN_CACHE_SECONDS, payload)
    return payload
