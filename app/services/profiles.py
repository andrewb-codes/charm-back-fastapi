from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.profile import Profile
from app.repositories.profiles import ProfileRepository
from app.schemas.profile import (
    EmailChangeRequest,
    ProfileUpdateRequest,
    PasswordChangeRequest,
)


class DuplicateEmailError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class ProfileVersionConflictError(Exception):
    pass


class InvalidCurrentPasswordError(Exception):
    pass


class SameEmailError(Exception):
    pass


class SamePasswordError(Exception):
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
        update_data = request.model_dump(exclude_unset=True)
        version = update_data.pop("version")

        if profile.version != version:
            raise ProfileVersionConflictError

        for field, value in update_data.items():
            setattr(profile, field, value)

        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def change_email(
        self, *, profile: Profile, request: EmailChangeRequest
    ) -> Profile:
        if profile.version != request.version:
            raise ProfileVersionConflictError

        if not verify_password(request.current_password, profile.password):
            raise InvalidCurrentPasswordError

        new_email = str(request.new_email).strip().lower()

        if new_email == profile.email:
            raise SameEmailError

        if await self.repository.exists_by_email(new_email):
            raise DuplicateEmailError

        profile.email = new_email
        profile.version += 1

        try:
            await self.session.commit()
            await self.session.refresh(profile)
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateEmailError from exc

        return profile

    async def change_password(
        self, *, profile: Profile, request: PasswordChangeRequest
    ) -> Profile:
        if profile.version != request.version:
            raise ProfileVersionConflictError

        if not verify_password(request.current_password, profile.password):
            raise InvalidCurrentPasswordError

        if verify_password(request.new_password, profile.password):
            raise SamePasswordError

        profile.password = hash_password(request.new_password)
        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def delete_profile(self, *, profile: Profile) -> None:
        await self.repository.delete(profile)
        await self.session.commit()
