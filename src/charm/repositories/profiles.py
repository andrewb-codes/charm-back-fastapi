from typing import cast

from sqlalchemy import and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from charm.models import Profile, ProfileLike, Role, Status


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def exists_by_email(self, email: str) -> bool:
        query = select(Profile.id).where(Profile.email == email)
        result = await self.session.scalar(query)
        return result is not None

    async def create(self, *, email: str, password_hash: str) -> Profile:
        profile = Profile(email=email, password=password_hash)
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def get_by_email(self, email: str) -> Profile | None:
        query = select(Profile).where(Profile.email == email)
        return cast(Profile | None, await self.session.scalar(query))

    async def get_by_id(self, profile_id: int) -> Profile | None:
        return cast(Profile | None, await self.session.get(Profile, profile_id))

    async def delete(self, profile: Profile) -> None:
        await self.session.delete(profile)

    async def get_next_charm_candidate(self, profile: Profile) -> Profile | None:
        like_join_condition = and_(
            ProfileLike.a_profile == func.least(profile.id, Profile.id),
            ProfileLike.b_profile == func.greatest(profile.id, Profile.id),
        )

        current_user_has_not_voted = or_(
            ProfileLike.a_profile.is_(None),
            and_(ProfileLike.a_profile == profile.id, ProfileLike.liked_a.is_(None)),
            and_(ProfileLike.b_profile == profile.id, ProfileLike.liked_b.is_(None)),
        )

        query = (
            select(Profile)
            .outerjoin(ProfileLike, like_join_condition)
            .where(Profile.id != profile.id)
            .where(Profile.status == Status.ACTIVE)
            .where(current_user_has_not_voted)
            .order_by(func.random())
            .limit(1)
        )

        if profile.gender is not None:
            query = query.where(Profile.gender.is_not(None), Profile.gender != profile.gender)

        return cast(Profile | None, await self.session.scalar(query))

    async def get_matches(self, profile_id: int, limit: int, offset: int) -> list[Profile]:
        matched_profile_id = case(
            (ProfileLike.a_profile == profile_id, ProfileLike.b_profile),
            (ProfileLike.b_profile == profile_id, ProfileLike.a_profile),
        )

        query = (
            select(Profile)
            .select_from(ProfileLike)
            .join(Profile, Profile.id == matched_profile_id)
            .where((ProfileLike.a_profile == profile_id) | (ProfileLike.b_profile == profile_id))
            .where(ProfileLike.liked_a.is_(True), ProfileLike.liked_b.is_(True))
            .order_by(ProfileLike.updated_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.scalars(query)
        return list(result)

    async def search_profiles(
        self,
        email_starts_with: str | None,
        name_starts_with: str | None,
        surname_starts_with: str | None,
        role: Role | None,
        status: Status | None,
        limit: int,
        offset: int,
    ) -> list[Profile]:
        query = select(Profile).order_by(Profile.id.asc()).limit(limit).offset(offset)

        if email_starts_with:
            query = query.where(Profile.email.ilike(f"{email_starts_with}%"))

        if name_starts_with:
            query = query.where(Profile.name.ilike(f"{name_starts_with}%"))

        if surname_starts_with:
            query = query.where(Profile.surname.ilike(f"{surname_starts_with}%"))

        if role is not None:
            query = query.where(Profile.role == role)

        if status is not None:
            query = query.where(Profile.status == status)

        result = await self.session.scalars(query)
        return list(result)
