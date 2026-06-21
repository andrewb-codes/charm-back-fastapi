from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db_session
from app.models.profile import Profile
from app.repositories.profiles import ProfileRepository
from app.services.charm import CharmService
from app.services.profiles import ProfileService

bearer_scheme = HTTPBearer(auto_error=False)


def get_profile_service(
    session: AsyncSession = Depends(get_db_session),
) -> ProfileService:
    return ProfileService(session)


def get_charm_service(
    session: AsyncSession = Depends(get_db_session),
) -> CharmService:
    return CharmService(session)


async def get_current_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Profile:
    if credentials is None:
        raise UnauthorizedError()

    try:
        payload = decode_access_token(credentials.credentials)
        profile_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise UnauthorizedError() from exc

    repository = ProfileRepository(session)
    profile = await repository.get_by_id(profile_id)

    if profile is None:
        raise UnauthorizedError()

    return profile
