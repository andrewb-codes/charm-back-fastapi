from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import RegistrationResponse, RegistrationRequest
from app.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/registration", tags=["Registration"])


@router.post(
    "", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegistrationRequest, session: AsyncSession = Depends(get_db_session)
) -> RegistrationResponse:
    service = ProfileService(session)

    profile_id = await service.register(
        email=str(request.email), password=request.password
    )

    return RegistrationResponse(id=profile_id)
