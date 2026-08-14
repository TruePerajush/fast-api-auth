import re
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import my_fast_api.infrastructure.services.password_hasher as hasher
from my_fast_api.dependencies import get_limiter
from my_fast_api.domain.entities import User
from my_fast_api.infrastructure.database import get_db_session


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
limiter = get_limiter()


@router.post(
    "/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db_session),
):
    email_lower = body.email.strip().lower()

    user = (
        await db.execute(select(User).where(User.email == email_lower))
    ).scalar_one_or_none()
    if user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Пользователь с таким email уже существует",
        )

    new_user = User(
        email=email_lower, password_hash=hasher.hash_password(body.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user
