from datetime import date

from app.api.deps import get_current_profile, get_charm_service
from app.models import Profile
from app.schemas.charm import CharmRequest, NextCharmResponse, CharmProfileResponse
from app.services.charm import CharmService
from fastapi import APIRouter, Depends, status

router = APIRouter(prefix="/api/v1/charm", tags=["Charm"])


def calculate_age(birthdate: date | None) -> int | None:
    if birthdate is None:
        return None

    today = date.today()
    age = today.year - birthdate.year

    if (today.month, today.day) < (birthdate.month, birthdate.day):
        age -= 1

    return age


def build_charm_profile_response(profile: Profile) -> CharmProfileResponse:
    return CharmProfileResponse(
        id=profile.id,
        name=profile.name,
        surname=profile.surname,
        birthdate=profile.birthdate,
        age=calculate_age(profile.birthdate),
        about=profile.about,
        photo=profile.photo,
    )


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def react(
    request: CharmRequest,
    profile: Profile = Depends(get_current_profile),
    service: CharmService = Depends(get_charm_service),
) -> None:
    await service.react(
        from_profile_id=profile.id,
        to_profile_id=request.to_profile_id,
        action=request.action,
    )


@router.get("", response_model=NextCharmResponse)
async def get_next(
    profile: Profile = Depends(get_current_profile),
    service: CharmService = Depends(get_charm_service),
) -> NextCharmResponse:
    candidate = await service.get_next(profile=profile)

    return NextCharmResponse(
        profile=build_charm_profile_response(candidate) if candidate else None
    )
