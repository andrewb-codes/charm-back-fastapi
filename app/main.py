from fastapi import FastAPI

from app.api.v1.registration import router as registration_router
from app.core.config import settings

app = FastAPI(title=settings.app_name)

app.include_router(registration_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
