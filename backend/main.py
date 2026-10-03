"""ARWA FastAPI application: configuration, CORS, and centralized error handling."""

import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from api.routes import router  # noqa: E402
from backend.services.errors import ArwaError  # noqa: E402

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("arwa")


def allowed_origins() -> list:
    """Comma-separated ALLOWED_ORIGINS, defaulting to the local frontend."""
    raw = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    return [origin.strip().rstrip("/") for origin in raw.split(",") if origin.strip()]


app = FastAPI(
    title="ARWA Academic Recovery API",
    description="Deterministic academic recovery engine with a grounded Groq agent.",
    version="3.0.0",
)

# Auth uses Bearer tokens (not cookies), so credentials are not needed cross-origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(ArwaError)
async def handle_arwa_error(_: Request, exc: ArwaError) -> JSONResponse:
    """Expected domain errors carry a safe, user-facing message."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Log the full error server-side; never send stack traces or internals to clients."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Something went wrong on our side. Please try again."})


app.include_router(router)
