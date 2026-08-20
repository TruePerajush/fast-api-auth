from fastapi import status
from httpx import AsyncClient


async def test_login_valid(
    get_test_user_data: tuple[str, str],
    client: AsyncClient,
):
    email, password = get_test_user_data
    _ = await client.post(
        url="/api/auth/register", json={"email": email, "password": password}
    )

    response = await client.post(
        url="/api/auth/login", json={"email": email, "password": password}
    )
    data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert data.get("access_token") is not None
    assert data.get("refresh_token") is not None
