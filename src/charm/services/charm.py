from sqlalchemy.ext.asyncio import AsyncSession

from charm.core.exceptions import SelfLikeError
from charm.models.profile import Profile
from charm.repositories.profile_likes import ProfileLikeRepository
from charm.repositories.profiles import ProfileRepository
from charm.schemas.charm import CharmAction


class CharmService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profile_repository = ProfileRepository(session)
        self.profile_like_repository = ProfileLikeRepository(session)

    async def react(self, *, from_profile_id: int, to_profile_id: int, action: CharmAction) -> None:
        if from_profile_id == to_profile_id:
            raise SelfLikeError()

        if action == CharmAction.SKIP:
            return

        await self.profile_like_repository.set_like(
            from_profile_id=from_profile_id,
            to_profile_id=to_profile_id,
            liked=action == CharmAction.LIKE,
        )

        await self.session.commit()

    async def get_next(self, *, profile: Profile) -> Profile | None:
        return await self.profile_repository.get_next_charm_candidate(profile)
