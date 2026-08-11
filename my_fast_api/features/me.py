import logging
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.dependencies import get_jwt_service
from my_fast_api.domain.entities import Session, User
from my_fast_api.infrastructure.database import get_db_session
from my_fast_api.infrastructure.services.jwt_service import JwtService, TokenPayload

router = APIRouter()
bearer_scheme = HTTPBearer()
logger = logging.getLogger(__name__)

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: EmailStr
    is_active: bool
    created_at: datetime


@router.get("/me", response_model=MeResponse, status_code=status.HTTP_200_OK)
async def me(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
    jwt_service: JwtService = Depends(get_jwt_service),
):
    payload: TokenPayload | None = jwt_service.verify_token(credentials.credentials)
    if not payload:
        logger.info("payload is none")
        raise CREDENTIALS_EXCEPTION

    if payload.token_type != "access":
        logger.info("payload type is not access")
        raise CREDENTIALS_EXCEPTION

    session = await db.get(Session, payload.session_id)
    now = datetime.now(UTC)
    if not session or session.revoked_at or session.expires_at < now:
        raise CREDENTIALS_EXCEPTION

    user = await db.get(User, payload.user_id)
    if not user or not user.is_active:
        raise CREDENTIALS_EXCEPTION

    return user
