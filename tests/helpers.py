from httpx import AsyncClient
from sqlalchemy import text

from charm.db.session import AsyncSessionLocal
from charm.rate_limit.rules import RateLimitRule
from charm.rate_limit.service import RateLimitResult


class FakeRateLimitService:
    enabled = True

    def __init__(self, *, denied_scope: str | None = None) -> None:
        self.denied_scope = denied_scope
        self.calls: list[tuple[RateLimitRule, str]] = []

    async def hit(self, *, rule: RateLimitRule, key: str, cost: int = 1) -> RateLimitResult:
        self.calls.append((rule, key))

        allowed = rule.scope != self.denied_scope

        return RateLimitResult(
            allowed=allowed,
            limit=1,
            remaining=0 if not allowed else 1,
            reset_at=123,
            retry_after=42,
        )


async def register_and_login(
    client: AsyncClient, email: str = "user@mail.com", password: str = "123456"
) -> str:
    await client.post(
        "/api/v1/registration",
        json={"email": email, "password": password},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )

    return str(response.json()["access_token"])


async def activate_profile(profile_id: int, name: str, surname: str, gender: str) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                """
                UPDATE profile
                SET status = 'ACTIVE',
                    name = :name,
                    surname = :surname,
                    gender = :gender
                WHERE id = :profile_id
                """
            ),
            {
                "profile_id": profile_id,
                "name": name,
                "surname": surname,
                "gender": gender,
            },
        )
        await session.commit()


async def make_admin(profile_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            text(
                """
                UPDATE profile
                SET role = 'ADMIN'
                WHERE id = :profile_id
                """
            ),
            {"profile_id": profile_id},
        )
        await session.commit()
