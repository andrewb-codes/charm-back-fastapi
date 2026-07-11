from fastapi import APIRouter, Depends, Query

from charm.api.deps import get_current_profile, get_profile_service
from charm.api.presenters.profile import build_public_profile_response
from charm.models import Profile
from charm.schemas.profile import MatchesResponse
from charm.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/matches", tags=["Matches"])


@router.get("", response_model=MatchesResponse)
async def get_matches(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    profile: Profile = Depends(get_current_profile),
    service: ProfileService = Depends(get_profile_service),
) -> MatchesResponse:
    items, has_next = await service.get_matches(
        profile_id=profile.id,
        page=page,
        page_size=page_size,
    )

    return MatchesResponse(
        items=[build_public_profile_response(item) for item in items],
        has_next=has_next,
    )
