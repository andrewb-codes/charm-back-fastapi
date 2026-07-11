from fastapi import APIRouter, Depends

from charm.api.deps import get_profile_service
from charm.core.config import settings
from charm.core.security import create_access_token
from charm.schemas.auth import LoginRequest, TokenResponse
from charm.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest, service: ProfileService = Depends(get_profile_service)
) -> TokenResponse:
    profile = await service.authenticate(email=str(request.email), password=request.password)

    access_token = create_access_token(
        user_id=profile.id, email=profile.email, role=profile.role.value
    )

    return TokenResponse(access_token=access_token, expires_in=settings.jwt_ttl_minutes * 60)
