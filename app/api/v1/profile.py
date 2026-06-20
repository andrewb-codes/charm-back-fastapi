from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_profile
from app.db.session import get_db_session
from app.models.profile import Profile
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest
from app.services.profiles import ProfileService, ProfileVersionConflictError

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
    session: AsyncSession = Depends(get_db_session),
) -> ProfileResponse:
    service = ProfileService(session)

    try:
        updated_profile = await service.update_profile(profile=profile, request=request)
    except ProfileVersionConflictError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="error.profile.version_conflict",
        ) from exc

    return build_profile_response(updated_profile)
