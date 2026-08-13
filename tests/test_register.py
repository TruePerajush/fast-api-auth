from httpx import AsyncClient


async def test_register_valid(client: AsyncClient):
    response = await client.post(url="/api/auth/register", json={})
