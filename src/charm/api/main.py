from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from charm.api.v1.admin_profiles import router as admin_profiles_router
from charm.api.v1.auth import router as auth_router
from charm.api.v1.charm import router as charm_router
from charm.api.v1.matches import router as matches_router
from charm.api.v1.profile import router as profile_router
from charm.api.v1.registration import router as registration_router
from charm.core.config import settings
from charm.core.exceptions import AppError
from charm.core.logging import configure_logging
from charm.middleware.request_logging import request_logging_middleware
from charm.rate_limit.service import RateLimitService

configure_logging(settings)
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("application_starting")

    rate_limiter = RateLimitService.from_settings(settings)

    if rate_limiter.enabled and not await rate_limiter.check_storage():
        logger.error("rate_limit_storage_unavailable")
        raise RuntimeError("Rate limit Redis storage is not available")

    app.state.rate_limiter = rate_limiter
    logger.info("application_started")

    try:
        yield
    finally:
        logger.info("application_stopping")
        app.state.rate_limiter = None
        logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "REST API for Charm: authentication, profiles, discovery, matches, "
        "and admin profile management."
    ),
    lifespan=lifespan,
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.middleware("http")(request_logging_middleware)

app.include_router(admin_profiles_router)
app.include_router(auth_router)
app.include_router(charm_router)
app.include_router(matches_router)
app.include_router(profile_router)
app.include_router(registration_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    headers = None

    if hasattr(exc, "retry_after"):
        headers = {"Retry-After": str(exc.retry_after)}

    return JSONResponse(
        status_code=exc.status_code, content={"detail": exc.detail}, headers=headers
    )
