import http
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.config import Settings, get_settings
from my_fast_api.dependencies import get_jwt_service, get_rate_limiter
from my_fast_api.domain.entities import Session, User
from my_fast_api.infrastructure.database import get_db_session
from my_fast_api.infrastructure.services import password_hasher
from my_fast_api.infrastructure.services.jwt_service import JwtService
from my_fast_api.infrastructure.services.rate_limit import RateLimiter


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


router = APIRouter()


@router.post("/login", response_model=LoginResponse, status_code=http.HTTPStatus.OK)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
    jwt_service: JwtService = Depends(get_jwt_service),
    settings: Settings = Depends(get_settings),
):
    check_result = await rate_limiter.check(
        "login_ip",
        request.client.host,  # type: ignore
        3,
        60,
    )
    if check_result:
        check_result.raise_error()
        return

    email_lower = body.email.strip().lower()
    check_result = await rate_limiter.check(
        "login_email",
        email_lower,  # type: ignore
        3,
        60,
    )
    if check_result:
        check_result.raise_error()
        return

    user = (
        await db.execute(select(User).where(User.email == email_lower))
    ).scalar_one_or_none()
    if not user or not password_hasher.verify_password(
        body.password, user.password_hash
    ):
        raise HTTPException(
            status_code=http.HTTPStatus.UNAUTHORIZED, detail="Invalid credentials"
        )

    session = Session(
        id=uuid.uuid7(),
        user_id=user.id,
        refresh_token_hash="",
        ip=request.client.host,  # type: ignore
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl),
    )
    access_token = jwt_service.generate_access_token(user.id, session.id)
    refresh_token = jwt_service.generate_refresh_token(user.id, session.id)
    session.refresh_token_hash = jwt_service.hash_token(refresh_token)
    db.add(session)
    await db.commit()
    await db.refresh(session)

    return LoginResponse(access_token=access_token, refresh_token=refresh_token)
