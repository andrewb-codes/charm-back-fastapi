from fastapi import APIRouter, Depends, status

from charm.api.deps import get_current_profile, get_profile_service
from charm.api.presenters.profile import build_profile_response
from charm.models.profile import Profile
from charm.rate_limit.deps import rate_limit_user
from charm.rate_limit.rules import PROFILE_READ_LIMIT, PROFILE_WRITE_LIMIT
from charm.schemas.profile import (
    EmailChangeRequest,
    PasswordChangeRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from charm.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
async def get_profile(
    profile: Profile = Depends(get_current_profile),
    _: None = Depends(rate_limit_user(PROFILE_READ_LIMIT)),
) -> ProfileResponse:
    return build_profile_response(profile)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    profile: Profile = Depends(get_current_profile),
    _: None = Depends(rate_limit_user(PROFILE_WRITE_LIMIT)),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.update_profile(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.patch("/email", response_model=ProfileResponse)
async def change_email(
    request: EmailChangeRequest,
    profile: Profile = Depends(get_current_profile),
    _: None = Depends(rate_limit_user(PROFILE_WRITE_LIMIT)),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.change_email(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.patch("/password", response_model=ProfileResponse)
async def change_password(
    request: PasswordChangeRequest,
    profile: Profile = Depends(get_current_profile),
    _: None = Depends(rate_limit_user(PROFILE_WRITE_LIMIT)),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.change_password(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile: Profile = Depends(get_current_profile),
    _: None = Depends(rate_limit_user(PROFILE_WRITE_LIMIT)),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    await service.delete_profile(profile=profile)
