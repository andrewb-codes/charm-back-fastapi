from app.api.deps import get_current_profile
from app.db.session import get_db_session
from app.models import Profile
from app.schemas.charm import CharmRequest
from app.services.charm import CharmService
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/charm", tags=["Charm"])


@router.post("", status_code=status.HTTP_204_NO_CONTENT)
async def react(
    request: CharmRequest,
    profile: Profile = Depends(get_current_profile),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    service = CharmService(session)

    await service.react(
        from_profile_id=profile.id,
        to_profile_id=request.to_profile_id,
        action=request.action,
    )
