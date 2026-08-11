from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.dependencies import get_db, get_jwt_service
from my_fast_api.domain.entities import Session
from my_fast_api.infrastructure.services.jwt_service import JwtService

router = APIRouter()
bearer_scheme = HTTPBearer()
CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
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
