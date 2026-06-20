from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.schemas.auth import TokenResponse, LoginRequest
from app.services.profiles import ProfileService, InvalidCredentialsError

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, session: AsyncSession = Depends(get_db_session)
) -> TokenResponse:
    service = ProfileService(session)

    try:
        profile = await service.authenticate(
            email=str(request.email), password=request.password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="error.credentials.invalid"
        ) from exc

    access_token = create_access_token(
        user_id=profile.id, email=profile.email, role=profile.role.value
    )

    return TokenResponse(
        access_token=access_token, expires_in=settings.jwt_ttl_minutes * 60
    )
