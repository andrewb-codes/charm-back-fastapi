from sqlalchemy import select
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
