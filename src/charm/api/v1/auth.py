from fastapi import APIRouter, Depends, Response

from charm.api.deps import get_profile_service
from charm.core.config import settings
from charm.core.exceptions import InvalidCredentialsError
from charm.core.security import create_access_token
from charm.rate_limit.deps import apply_rate_limit, get_rate_limit_service
from charm.rate_limit.keys import build_global_key, build_identifier_key, require_key_secret
from charm.rate_limit.rules import LOGIN_ACCOUNT_LIMIT, LOGIN_GLOBAL_LIMIT
from charm.rate_limit.service import RateLimitService
from charm.schemas.auth import LoginRequest, TokenResponse
from charm.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    response: Response,
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
    service: ProfileService = Depends(get_profile_service),
) -> TokenResponse:
    await apply_rate_limit(
        rule=LOGIN_GLOBAL_LIMIT,
        key_factory=lambda: build_global_key(scope=LOGIN_GLOBAL_LIMIT.scope),
        response=response,
        service=rate_limit_service,
    )

    try:
        profile = await service.authenticate(email=str(request.email), password=request.password)
    except InvalidCredentialsError:
        await apply_rate_limit(
            rule=LOGIN_ACCOUNT_LIMIT,
            key_factory=lambda: build_identifier_key(
                scope=LOGIN_ACCOUNT_LIMIT.scope,
                identifier_kind="email",
                identifier=str(request.email),
                secret=require_key_secret(settings.rate_limit_key_secret),
            ),
            response=response,
            service=rate_limit_service,
        )
        raise

    access_token = create_access_token(
        user_id=profile.id, email=profile.email, role=profile.role.value
    )

    return TokenResponse(access_token=access_token, expires_in=settings.jwt_ttl_minutes * 60)
