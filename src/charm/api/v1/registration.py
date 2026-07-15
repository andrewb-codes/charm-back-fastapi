from fastapi import APIRouter, Depends, Response, status

from charm.api.deps import get_profile_service
from charm.core.config import settings
from charm.rate_limit.deps import apply_rate_limit, get_rate_limit_service
from charm.rate_limit.keys import build_global_key, build_identifier_key, require_key_secret
from charm.rate_limit.rules import REGISTER_GLOBAL_LIMIT, REGISTER_IDENTIFIER_LIMIT
from charm.rate_limit.service import RateLimitService
from charm.schemas.auth import RegistrationRequest, RegistrationResponse
from charm.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/registration", tags=["Registration"])


@router.post("", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegistrationRequest,
    response: Response,
    rate_limit_service: RateLimitService = Depends(get_rate_limit_service),
    service: ProfileService = Depends(get_profile_service),
) -> RegistrationResponse:
    await apply_rate_limit(
        rule=REGISTER_GLOBAL_LIMIT,
        key_factory=lambda: build_global_key(scope=REGISTER_GLOBAL_LIMIT.scope),
        response=response,
        service=rate_limit_service,
    )
    await apply_rate_limit(
        rule=REGISTER_IDENTIFIER_LIMIT,
        key_factory=lambda: build_identifier_key(
            scope=REGISTER_IDENTIFIER_LIMIT.scope,
            identifier_kind="email",
            identifier=str(request.email),
            secret=require_key_secret(settings.rate_limit_key_secret),
        ),
        response=response,
        service=rate_limit_service,
    )

    profile_id = await service.register(email=str(request.email), password=request.password)

    return RegistrationResponse(id=profile_id)
