from fastapi import APIRouter, Depends, status

from app.api.deps import get_profile_service
from app.schemas.auth import RegistrationResponse, RegistrationRequest
from app.services.profiles import ProfileService

router = APIRouter(prefix="/api/v1/registration", tags=["Registration"])


@router.post(
    "", response_model=RegistrationResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    request: RegistrationRequest,
    service: ProfileService = Depends(get_profile_service),
) -> RegistrationResponse:
    profile_id = await service.register(
        email=str(request.email), password=request.password
    )

    return RegistrationResponse(id=profile_id)
