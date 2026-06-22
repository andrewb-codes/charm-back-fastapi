from httpx import AsyncClient

from tests.helpers import activate_profile, register_and_login

PUBLIC_PROFILE_FIELDS = {
    "id",
    "name",
    "surname",
    "birthdate",
    "age",
    "about",
    "gender",
    "photo",
}


async def test_get_charm_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/charm")

    assert response.status_code == 401
    assert response.json() == {"detail": "error.auth.unauthorized"}


async def test_get_charm_returns_active_candidate(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    response = await client.get(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert set(body) == {"profile"}
    assert body["profile"] is not None
    assert set(body["profile"]) == PUBLIC_PROFILE_FIELDS
    assert body["profile"]["id"] == 2
    assert body["profile"]["name"] == "User"
    assert body["profile"]["surname"] == "Two"
    assert body["profile"]["gender"] == "FEMALE"


async def test_charm_self_like_returns_400(client: AsyncClient) -> None:
    token = await register_and_login(client)

    response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token}"},
        json={"to_profile_id": 1, "action": "like"},
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "error.charm.self_like"}


async def test_get_matches_without_token_returns_401(client: AsyncClient) -> None:
    response = await client.get("/api/v1/matches")

    assert response.status_code == 401
    assert response.json() == {"detail": "error.auth.unauthorized"}


async def test_one_sided_like_does_not_create_match(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    like_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "like"},
    )
    matches_response = await client.get(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    assert like_response.status_code == 204
    assert matches_response.status_code == 200
    assert matches_response.json() == {"items": [], "has_next": False}


async def test_dislike_does_not_create_match(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    dislike_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "dislike"},
    )
    matches_response = await client.get(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    assert dislike_response.status_code == 204
    assert matches_response.status_code == 200
    assert matches_response.json() == {"items": [], "has_next": False}


async def test_skip_does_not_create_match(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    skip_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "skip"},
    )
    matches_response = await client.get(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    assert skip_response.status_code == 204
    assert matches_response.status_code == 200
    assert matches_response.json() == {"items": [], "has_next": False}


async def test_mutual_like_creates_match(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    token_2 = await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    first_like_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "like"},
    )
    second_like_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"to_profile_id": 1, "action": "like"},
    )

    matches_response = await client.get(
        "/api/v1/matches",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    body = matches_response.json()

    assert first_like_response.status_code == 204
    assert second_like_response.status_code == 204
    assert matches_response.status_code == 200
    assert set(body) == {"items", "has_next"}
    assert body["has_next"] is False
    assert len(body["items"]) == 1
    assert set(body["items"][0]) == PUBLIC_PROFILE_FIELDS
    assert body["items"][0]["id"] == 2
    assert "email" not in body["items"][0]


async def test_get_charm_returns_null_when_no_candidates(client: AsyncClient) -> None:
    token = await register_and_login(client, email="user1@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")

    response = await client.get(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json() == {"profile": None}


async def test_reacted_candidate_is_not_returned_again(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    await register_and_login(client, email="user2@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")

    first_response = await client.get(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
    )
    like_response = await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "like"},
    )
    second_response = await client.get(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    assert first_response.status_code == 200
    assert first_response.json()["profile"]["id"] == 2
    assert like_response.status_code == 204
    assert second_response.status_code == 200
    assert second_response.json() == {"profile": None}


async def test_matches_pagination_has_next(client: AsyncClient) -> None:
    token_1 = await register_and_login(client, email="user1@mail.com")
    token_2 = await register_and_login(client, email="user2@mail.com")
    token_3 = await register_and_login(client, email="user3@mail.com")

    await activate_profile(1, name="User", surname="One", gender="MALE")
    await activate_profile(2, name="User", surname="Two", gender="FEMALE")
    await activate_profile(3, name="User", surname="Three", gender="FEMALE")

    await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 2, "action": "like"},
    )
    await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"to_profile_id": 1, "action": "like"},
    )

    await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_1}"},
        json={"to_profile_id": 3, "action": "like"},
    )
    await client.post(
        "/api/v1/charm",
        headers={"Authorization": f"Bearer {token_3}"},
        json={"to_profile_id": 1, "action": "like"},
    )

    first_page_response = await client.get(
        "/api/v1/matches?page=1&page_size=1",
        headers={"Authorization": f"Bearer {token_1}"},
    )
    second_page_response = await client.get(
        "/api/v1/matches?page=2&page_size=1",
        headers={"Authorization": f"Bearer {token_1}"},
    )

    first_page = first_page_response.json()
    second_page = second_page_response.json()

    assert first_page_response.status_code == 200
    assert second_page_response.status_code == 200

    assert len(first_page["items"]) == 1
    assert first_page["has_next"] is True

    assert len(second_page["items"]) == 1
    assert second_page["has_next"] is False

    assert first_page["items"][0]["id"] != second_page["items"][0]["id"]
