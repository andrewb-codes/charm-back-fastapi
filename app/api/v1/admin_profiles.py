from fastapi import APIRouter, Depends, Query

from app.api.deps import get_profile_service, require_admin
from app.api.presenters.profile import build_profile_response
from app.models import Profile, Role, Status
from app.schemas.profile import (
    AdminProfilesPageResponse,
    ProfileResponse,
    AdminProfileStatusUpdateRequest,
    AdminProfileRoleUpdateRequest,
)
from app.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/admin/profiles", tags=["Admin Profiles"])


@router.get("", response_model=AdminProfilesPageResponse)
async def search_profiles(
    email_starts_with: str | None = None,
    name_starts_with: str | None = None,
    surname_starts_with: str | None = None,
    role: Role | None = None,
    status: Status | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    _: Profile = Depends(require_admin),
    service: ProfileService = Depends(get_profile_service),
) -> AdminProfilesPageResponse:
    items, has_next = await service.search_profiles(
        email_starts_with=email_starts_with,
        name_starts_with=name_starts_with,
        surname_starts_with=surname_starts_with,
        role=role,
        status=status,
        page=page,
        page_size=page_size,
    )

    return AdminProfilesPageResponse(
        items=[build_profile_response(item) for item in items],
        has_next=has_next,
    )


@router.patch("/{profile_id}/status", response_model=ProfileResponse)
async def change_profile_status(
    profile_id: int,
    request: AdminProfileStatusUpdateRequest,
    admin_profile: Profile = Depends(require_admin),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    profile = await service.change_profile_status(
        admin_profile=admin_profile,
        profile_id=profile_id,
        request=request,
    )

    return build_profile_response(profile)


@router.patch("/{profile_id}/role", response_model=ProfileResponse)
async def change_profile_role(
    profile_id: int,
    request: AdminProfileRoleUpdateRequest,
    admin_profile: Profile = Depends(require_admin),
    service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    profile = await service.change_profile_role(
        admin_profile=admin_profile,
        profile_id=profile_id,
        request=request,
    )

    return build_profile_response(profile)
