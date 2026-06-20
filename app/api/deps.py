from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import InvalidTokenError, decode_access_token
from app.db.session import get_db_session
from app.models.profile import Profile
from app.repositories.profiles import ProfileRepository

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_profile(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> Profile:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = decode_access_token(credentials.credentials)
        profile_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, ValueError) as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED) from exc

    repository = ProfileRepository(session)
    profile = await repository.get_by_id(profile_id)

    if profile is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return profile
