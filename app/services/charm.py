from app.core.exceptions import SelfLikeError
from app.repositories.profile_likes import ProfileLikeRepository
from app.schemas.charm import CharmAction
from sqlalchemy.ext.asyncio import AsyncSession


class CharmService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ProfileLikeRepository(session)

    async def react(
        self, *, from_profile_id: int, to_profile_id: int, action: CharmAction
    ) -> None:
        if from_profile_id == to_profile_id:
            raise SelfLikeError()

        if action == CharmAction.SKIP:
            return

        await self.repository.set_like(
            from_profile_id=from_profile_id,
            to_profile_id=to_profile_id,
            liked=action == CharmAction.LIKE,
        )

        await self.session.commit()
