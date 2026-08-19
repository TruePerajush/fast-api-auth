import uuid
from datetime import UTC, datetime, timedelta

from fastapi import Request, status
from fastapi.param_functions import Depends
from fastapi.routing import APIRouter
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from application.common.errors import CREDENTIALS_EXCEPTION
from application.config import Settings, get_settings
from application.dependencies import get_jwt_service, get_limiter
from application.domain.entities import Session, User
from application.infrastructure.database import get_db_session
from application.infrastructure.services.jwt_service import JwtService

router = APIRouter()
limiter = get_limiter()


class RefreshRequest(BaseModel):
    refresh_token: str


class RefreshResponse(BaseModel):
    access_token: str
    refresh_token: str


@router.post("/refresh", response_model=RefreshResponse, status_code=status.HTTP_200_OK)
@limiter.limit("5/minute")
async def refresh(
    body: RefreshRequest,
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    jwt_service: JwtService = Depends(get_jwt_service),
    settings: Settings = Depends(get_settings),
):
    payload = jwt_service.verify_token(body.refresh_token)
    if not payload or payload.token_type != "refresh":
        raise CREDENTIALS_EXCEPTION

    session = await db.get(Session, payload.session_id)
    now = datetime.now(UTC)
    if (
        session is None
        or session.revoked_at is not None
        or session.expires_at < now
        or session.refresh_token_hash != jwt_service.hash_token(body.refresh_token)
    ):
        raise CREDENTIALS_EXCEPTION

    user = await db.get(User, session.user_id)
    if not (user and user.is_active):
        raise CREDENTIALS_EXCEPTION

    session.revoked_at = now
    session.refresh_token_hash = ""

    new_session = Session(
        id=uuid.uuid7(),
        user_id=user.id,
        refresh_token_hash="",
        ip=request.client.host,  # type: ignore
        user_agent=request.headers.get("user-agent"),
        expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_ttl),
    )
    access_token = jwt_service.generate_access_token(user.id, new_session.id)
    refresh_token = jwt_service.generate_refresh_token(user.id, new_session.id)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    return RefreshResponse(access_token=access_token, refresh_token=refresh_token)
