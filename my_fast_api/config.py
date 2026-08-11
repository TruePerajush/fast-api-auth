from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    redis_url: str

    jwt_secret: str
    jwt_issuer: str
    jwt_audience: str

    access_token_ttl: int
    refresh_token_ttl: int

    login_max_failed_attempts: int
    login_lockout_minutes: int

    environment: str
    debug: bool

    model_config = SettingsConfigDict(env_file=".env.example")

@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore
