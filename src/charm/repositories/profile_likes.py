from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from charm.models.profile_like import ProfileLike


class ProfileLikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def set_like(
        self,
        *,
        from_profile_id: int,
        to_profile_id: int,
        liked: bool,
    ) -> None:
        a_profile = min(from_profile_id, to_profile_id)
        b_profile = max(from_profile_id, to_profile_id)

        values: dict[str, int | bool | None] = {
            "a_profile": a_profile,
            "b_profile": b_profile,
            "liked_a": liked if from_profile_id == a_profile else None,
            "liked_b": liked if from_profile_id == b_profile else None,
        }

        statement = insert(ProfileLike).values(**values)

        update_values: dict[str, Any] = {"updated_at": func.now()}

        if from_profile_id == a_profile:
            update_values["liked_a"] = liked
        else:
            update_values["liked_b"] = liked

        statement = statement.on_conflict_do_update(
            index_elements=[ProfileLike.a_profile, ProfileLike.b_profile],
            set_=update_values,
        )

        await self.session.execute(statement)
