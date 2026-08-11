import hashlib
import logging
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import jwt

from my_fast_api.config import Settings

logger = logging.getLogger(__name__)


@dataclass
class TokenPayload:
    user_id: uuid.UUID
    session_id: uuid.UUID
    token_type: str


class JwtService:
    def __init__(self, settings: Settings) -> None:
        self.secret = settings.jwt_secret
        self.issuer = settings.jwt_issuer
        self.audience = settings.jwt_audience
        self.expiration = settings.access_token_ttl

    @staticmethod
    def hash_token(token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_access_token(self, user_id: uuid.UUID, session_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(minutes=self.expiration)

        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "iss": self.issuer,
            "aud": self.audience,
            "exp": int(expires_at.timestamp()),
            "iat": int(now.timestamp()),
            "type": "access",
        }

        return jwt.encode(payload, self.secret, algorithm="HS256")

    def generate_refresh_token(self, user_id: uuid.UUID, session_id: uuid.UUID) -> str:
        now = datetime.now(UTC)
        expires_at = now + timedelta(days=self.expiration)

        payload = {
            "sub": str(user_id),
            "sid": str(session_id),
            "iss": self.issuer,
            "aud": self.audience,
            "exp": int(expires_at.timestamp()),
            "iat": int(now.timestamp()),
            "type": "refresh",
        }

        return jwt.encode(payload, self.secret, algorithm="HS256")

    def decode_token(self, token: str) -> dict:
        return jwt.decode(
            token,
            self.secret,
            algorithms=["HS256"],
            issuer=self.issuer,
            audience=self.audience,
        )

    def verify_token(self, token: str) -> TokenPayload | None:
        try:
            payload = jwt.decode(
                token,
                self.secret,
                algorithms=["HS256"],
                issuer=self.issuer,
                audience=self.audience,
            )
            return TokenPayload(
                user_id=uuid.UUID(payload["sub"]),
                session_id=uuid.UUID(payload["sid"]),
                token_type=payload["type"],
            )
        except (jwt.InvalidTokenError, jwt.DecodeError, KeyError, ValueError) as e:
            logger.info("token is invalid")
            logger.debug(e)
            return None


jwt_service = JwtService()
