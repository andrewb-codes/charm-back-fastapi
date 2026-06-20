from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.profile import Profile
from app.repositories.profiles import ProfileRepository
from app.schemas.profile import ProfileUpdateRequest


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class ProfileNotFoundError(Exception):
    pass


class ProfileVersionConflictError(Exception):
    pass


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProfileRepository(session)

    async def register(self, *, email: str, password: str) -> int:
        normalized_email = email.strip().lower()

        if await self.repository.exists_by_email(normalized_email):
            raise DuplicateEmailError

        password_hash = hash_password(password)

        try:
            profile = await self.repository.create(
                email=normalized_email, password_hash=password_hash
            )
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateEmailError from exc

        return profile.id

    async def authenticate(self, *, email: str, password: str) -> Profile:
        normalized_email = email.strip().lower()
        profile = await self.repository.get_by_email(normalized_email)

        if profile is None:
            raise InvalidCredentialsError

        if not verify_password(password, profile.password):
            raise InvalidCredentialsError

        return profile

    async def update_profile(
        self, *, profile: Profile, request: ProfileUpdateRequest
    ) -> Profile:
        if profile.version != request.version:
            raise ProfileVersionConflictError

        profile.name = request.name
        profile.surname = request.surname
        profile.birthdate = request.birthdate
        profile.about = request.about
        profile.gender = request.gender
        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile
