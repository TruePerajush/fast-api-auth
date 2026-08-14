from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.common.errors import CREDENTIALS_EXCEPTION
from my_fast_api.dependencies import get_jwt_service, get_limiter
from my_fast_api.domain.entities import Session
from my_fast_api.infrastructure.database import get_db_session
from my_fast_api.infrastructure.services.jwt_service import JwtService

router = APIRouter()
limiter = get_limiter()
bearer_scheme = HTTPBearer()


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db_session),
    jwt_service: JwtService = Depends(get_jwt_service),
):
    payload = jwt_service.verify_token(credentials.credentials)
    if not payload:
        raise CREDENTIALS_EXCEPTION

    if payload.token_type != "access":
        raise CREDENTIALS_EXCEPTION

    now = datetime.now(UTC)
    session = await db.get(Session, payload.session_id)
    if not session or session.revoked_at or session.expires_at < now:
        raise CREDENTIALS_EXCEPTION

    session.revoked_at = now
    session.refresh_token_hash = ""
    await db.commit()
    await db.refresh(session)
