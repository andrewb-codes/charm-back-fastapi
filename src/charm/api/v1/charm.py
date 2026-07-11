from fastapi import APIRouter, Depends, status

from charm.api.deps import get_charm_service, get_current_profile
from charm.api.presenters.profile import build_public_profile_response
from charm.models import Profile
from charm.schemas.charm import CharmRequest, NextCharmResponse
from charm.services.charm import CharmService

router = APIRouter(prefix="/api/v1/charm", tags=["Charm"])


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
        profile=build_public_profile_response(candidate) if candidate else None
    )
