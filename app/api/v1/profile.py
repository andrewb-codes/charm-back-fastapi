from datetime import date

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_profile, get_profile_service
from app.models.profile import Profile
from app.schemas.profile import (
    ProfileResponse,
    ProfileUpdateRequest,
    EmailChangeRequest,
    PasswordChangeRequest,
)
from app.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/profile", tags=["Profile"])


def calculate_age(birthdate: date | None) -> int | None:
    if birthdate is None:
        return None

    today = date.today()
    age = today.year - birthdate.year

    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def build_profile_response(profile: Profile) -> ProfileResponse:
    return ProfileResponse(
        id=profile.id,
        email=profile.email,
        name=profile.name,
        surname=profile.surname,
        birthdate=profile.birthdate,
        age=calculate_age(profile.birthdate),
        about=profile.about,
        gender=profile.gender,
        photo=profile.photo,
        status=profile.status,
        role=profile.role,
        version=profile.version,
        created_at=profile.created_at,
    )


@router.get("", response_model=ProfileResponse)
async def get_profile(
    profile: Profile = Depends(get_current_profile),
) -> ProfileResponse:
    return build_profile_response(profile)


@router.patch("", response_model=ProfileResponse)
async def update_profile(
    request: ProfileUpdateRequest,
    profile: Profile = Depends(get_current_profile),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.update_profile(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.patch("/email", response_model=ProfileResponse)
async def change_email(
    request: EmailChangeRequest,
    profile: Profile = Depends(get_current_profile),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.change_email(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.patch("/password", response_model=ProfileResponse)
async def change_password(
    request: PasswordChangeRequest,
    profile: Profile = Depends(get_current_profile),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    updated_profile = await service.change_password(profile=profile, request=request)
    return build_profile_response(updated_profile)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile: Profile = Depends(get_current_profile),
    service: ProfileService = Depends(get_profile_service),
) -> None:
    await service.delete_profile(profile=profile)
