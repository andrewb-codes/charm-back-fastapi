from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AdminSelfModificationError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidCurrentPasswordError,
    ProfileNotFoundError,
    ProfileVersionConflictError,
    SameEmailError,
    SamePasswordError,
)
from app.core.security import hash_password, verify_password
from app.models.profile import Profile, Role, Status
from app.repositories.profiles import ProfileRepository
from app.schemas.profile import (
    AdminProfileRoleUpdateRequest,
    AdminProfileStatusUpdateRequest,
    EmailChangeRequest,
    PasswordChangeRequest,
    ProfileUpdateRequest,
)


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProfileRepository(session)

    async def register(self, *, email: str, password: str) -> int:
        normalized_email = email.strip().lower()

        if await self.repository.exists_by_email(normalized_email):
            raise DuplicateEmailError()

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
            raise InvalidCredentialsError()

        if not verify_password(password, profile.password):
            raise InvalidCredentialsError()

        return profile

    async def update_profile(self, *, profile: Profile, request: ProfileUpdateRequest) -> Profile:
        update_data = request.model_dump(exclude_unset=True)
        version = update_data.pop("version")

        if profile.version != version:
            raise ProfileVersionConflictError()

        for field, value in update_data.items():
            setattr(profile, field, value)

        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def change_email(self, *, profile: Profile, request: EmailChangeRequest) -> Profile:
        if profile.version != request.version:
            raise ProfileVersionConflictError()

        if not verify_password(request.current_password, profile.password):
            raise InvalidCurrentPasswordError()

        new_email = str(request.new_email).strip().lower()

        if new_email == profile.email:
            raise SameEmailError()

        if await self.repository.exists_by_email(new_email):
            raise DuplicateEmailError()

        profile.email = new_email
        profile.version += 1

        try:
            await self.session.commit()
            await self.session.refresh(profile)
        except IntegrityError as exc:
            await self.session.rollback()
            raise DuplicateEmailError from exc

        return profile

    async def change_password(self, *, profile: Profile, request: PasswordChangeRequest) -> Profile:
        if profile.version != request.version:
            raise ProfileVersionConflictError()

        if not verify_password(request.current_password, profile.password):
            raise InvalidCurrentPasswordError()

        if verify_password(request.new_password, profile.password):
            raise SamePasswordError()

        profile.password = hash_password(request.new_password)
        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def delete_profile(self, *, profile: Profile) -> None:
        await self.repository.delete(profile)
        await self.session.commit()

    async def get_matches(
        self, *, profile_id: int, page: int, page_size: int
    ) -> tuple[list[Profile], bool]:
        normalized_page = max(page, 1)
        normalized_page_size = max(page_size, 1)

        limit = normalized_page_size + 1
        offset = (normalized_page - 1) * normalized_page_size

        items = await self.repository.get_matches(
            profile_id=profile_id,
            limit=limit,
            offset=offset,
        )

        has_next = len(items) > normalized_page_size

        if has_next:
            items = items[:normalized_page_size]

        return items, has_next

    async def search_profiles(
        self,
        *,
        email_starts_with: str | None,
        name_starts_with: str | None,
        surname_starts_with: str | None,
        role: Role | None,
        status: Status | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Profile], bool]:
        normalized_page = max(page, 1)
        normalized_page_size = max(page_size, 1)

        limit = normalized_page_size + 1
        offset = (normalized_page - 1) * normalized_page_size

        items = await self.repository.search_profiles(
            email_starts_with=email_starts_with,
            name_starts_with=name_starts_with,
            surname_starts_with=surname_starts_with,
            role=role,
            status=status,
            limit=limit,
            offset=offset,
        )

        has_next = len(items) > normalized_page_size

        if has_next:
            items = items[:normalized_page_size]

        return items, has_next

    async def change_profile_status(
        self,
        *,
        admin_profile: Profile,
        profile_id: int,
        request: AdminProfileStatusUpdateRequest,
    ) -> Profile:
        if admin_profile.id == profile_id:
            raise AdminSelfModificationError()

        profile = await self.repository.get_by_id(profile_id)

        if profile is None:
            raise ProfileNotFoundError()

        if profile.version != request.version:
            raise ProfileVersionConflictError()

        profile.status = request.status
        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile

    async def change_profile_role(
        self,
        *,
        admin_profile: Profile,
        profile_id: int,
        request: AdminProfileRoleUpdateRequest,
    ) -> Profile:
        if admin_profile.id == profile_id:
            raise AdminSelfModificationError()

        profile = await self.repository.get_by_id(profile_id)

        if profile is None:
            raise ProfileNotFoundError()

        if profile.version != request.version:
            raise ProfileVersionConflictError()

        profile.role = request.role
        profile.version += 1

        await self.session.commit()
        await self.session.refresh(profile)

        return profile
