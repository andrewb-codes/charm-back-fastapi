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

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description=(
        "REST API for Charm: authentication, profiles, discovery, matches, "
        "and admin profile management."
    ),
)

if settings.cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
