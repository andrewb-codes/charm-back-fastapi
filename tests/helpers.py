from httpx import AsyncClient


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
