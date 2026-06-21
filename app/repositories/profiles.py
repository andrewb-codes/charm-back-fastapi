from app.models import ProfileLike, Status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import Profile


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
        return await self.session.scalar(query)

    async def get_by_id(self, profile_id: int) -> Profile | None:
        return await self.session.get(Profile, profile_id)

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
            query = query.where(
                Profile.gender.is_not(None), Profile.gender != profile.gender
            )

        return await self.session.scalar(query)
