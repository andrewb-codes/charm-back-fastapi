from collections.abc import AsyncGenerator

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from charm.api.main import app
from charm.db.session import AsyncSessionLocal


@pytest.fixture(autouse=True)
async def clean_db() -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(text("TRUNCATE TABLE profile_like, profile RESTART IDENTITY CASCADE"))
        await session.commit()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with (
        LifespanManager(app),
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client,
    ):
        yield client
