from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.domain.entities import User


async def test_register_valid(
    client: AsyncClient,
    get_test_user_data: tuple[str, str],
    db_session: AsyncSession,
):
    email, password = get_test_user_data

    response = await client.post(
        url="/api/auth/register", json={"email": email, "password": password}
    )
    data = response.json()
    result = (await db_session.execute(select(User).where(User.email == email))).all()

    assert data["email"] == email
    assert data["is_active"] == True
    assert len(result) == 1
