import http
import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.infrastructure.database import get_db_session
import my_fast_api.infrastructure.services.password_hasher as hasher
from my_fast_api.dependencies import get_rate_limiter
from my_fast_api.domain.entities import User
from my_fast_api.infrastructure.services.rate_limit import RateLimiter


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=50)

    @field_validator("password")
    @classmethod
    def is_password_valid(cls, v: str) -> str:
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError("Пароль должен содержать хотя бы один специальный символ")
        if not re.search(r"\d", v):
            raise ValueError("Пароль должен содержать хотя бы одну цифру")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Пароль должен содержать хотя бы одну заглавную букву")
        return v


class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime


router = APIRouter()


@router.post(
    "/register", response_model=RegisterResponse, status_code=http.HTTPStatus.CREATED
)
async def register(
    body: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
):
    check_result = await rate_limiter.check(
        "register_ip",
        request.client.host,  # type: ignore
        3,
        60,
    )
    if check_result:
        check_result.raise_error()
        return

    email_lower = body.email.strip().lower()

    db_result = await db.execute(select(User).where(User.email == email_lower))
    user = db_result.scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=http.HTTPStatus.CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    new_user = User(
        email=email_lower, password_hash=hasher.hash_password(body.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
