from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.auth import RegistrationResponse, RegistrationRequest
from app.services.profiles import ProfileService, DuplicateEmailError

router = APIRouter(prefix="/api/v1/registration", tags=["Registration"])


@router.post(
    "", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegistrationRequest, session: AsyncSession = Depends(get_db_session)
) -> RegistrationResponse:
    service = ProfileService(session)

    try:
        profile_id = await service.register(
            email=str(request.email), password=request.password
        )
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="error.email.exists"
        ) from exc

    return RegistrationResponse(id=profile_id)
