from httpx import AsyncClient

from charm.api.main import app
from charm.rate_limit.deps import get_rate_limit_service
from charm.rate_limit.rules import CHARM_REACT_LIMIT, CHARM_READ_LIMIT, MATCHES_READ_LIMIT
from tests.helpers import FakeRateLimitService, activate_profile, register_and_login


async def test_get_charm_applies_charm_read_rate_limit(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")
    await activate_profile(1, "Alice", "Smith", "FEMALE")
    await activate_profile(2, "Bob", "Brown", "MALE")

    service = FakeRateLimitService()
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.get(
            "/api/v1/charm",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 200

    rule, key = service.calls[0]

    assert rule.scope == CHARM_READ_LIMIT.scope
    assert key == "rate-limit:charm_read:user:1"


async def test_get_charm_returns_429_when_rate_limit_exceeded(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")

    service = FakeRateLimitService(denied_scope=CHARM_READ_LIMIT.scope)
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.get(
            "/api/v1/charm",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 429
    assert response.json() == {"detail": "error.rate_limit.exceeded"}
    assert response.headers["Retry-After"] == "42"


async def test_react_applies_charm_react_rate_limit(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    service = FakeRateLimitService()
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.post(
            "/api/v1/charm",
            headers={"Authorization": f"Bearer {token}"},
            json={"to_profile_id": 2, "action": "like"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 204

    rule, key = service.calls[0]

    assert rule.scope == CHARM_REACT_LIMIT.scope
    assert key == "rate-limit:charm_react:user:1"


async def test_react_returns_429_when_rate_limit_exceeded(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    service = FakeRateLimitService(denied_scope=CHARM_REACT_LIMIT.scope)
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.post(
            "/api/v1/charm",
            headers={"Authorization": f"Bearer {token}"},
            json={"to_profile_id": 2, "action": "like"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 429
    assert response.json() == {"detail": "error.rate_limit.exceeded"}
    assert response.headers["Retry-After"] == "42"


async def test_get_matches_applies_matches_read_rate_limit(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")

    service = FakeRateLimitService()
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.get(
            "/api/v1/matches",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 200

    rule, key = service.calls[0]

    assert rule.scope == MATCHES_READ_LIMIT.scope
    assert key == "rate-limit:matches_read:user:1"


async def test_get_matches_returns_429_when_rate_limit_exceeded(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")

    service = FakeRateLimitService(denied_scope=MATCHES_READ_LIMIT.scope)
    app.dependency_overrides[get_rate_limit_service] = lambda: service

    try:
        response = await client.get(
            "/api/v1/matches",
            headers={"Authorization": f"Bearer {token}"},
        )
    finally:
        app.dependency_overrides.pop(get_rate_limit_service, None)

    assert response.status_code == 429
    assert response.json() == {"detail": "error.rate_limit.exceeded"}
    assert response.headers["Retry-After"] == "42"
