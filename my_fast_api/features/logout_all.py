from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from my_fast_api.dependencies import get_db, get_jwt_service
from my_fast_api.domain.entities import Session
from my_fast_api.infrastructure.services.jwt_service import JwtService

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
)

router = APIRouter()
bearer_scheme = HTTPBearer()


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    credentials: HTTPAuthorizationCredentials = Security(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    jwt_service: JwtService = Depends(get_jwt_service),
):
    payload = jwt_service.verify_token(credentials.credentials)
    if not payload or payload.token_type != "access":
        raise CREDENTIALS_EXCEPTION

    await db.execute(
        update(Session)
        .where(Session.user_id == payload.user_id, Session.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC), refresh_token_hash="")
    )
    await db.commit()
