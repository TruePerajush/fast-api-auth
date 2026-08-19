import http
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from application.config import Settings, get_settings
from application.dependencies import get_jwt_service, get_limiter
from application.domain.entities import Session, User
from application.infrastructure.database import get_db_session
from application.infrastructure.services import password_hasher
from application.infrastructure.services.jwt_service import JwtService

router = APIRouter()
limiter = get_limiter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    jwt_service: JwtService = Depends(get_jwt_service),
    settings: Settings = Depends(get_settings),
):
    email_lower = body.email.strip().lower()

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
