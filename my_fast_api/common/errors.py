import http
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from fastapi import HTTPException


@dataclass(frozen=True, slots=True)
class AppError:
    """Базовый класс доменных ошибок сервиса"""

    status_code: http.HTTPStatus
    code: str
    message: str

    @staticmethod
    def raise_if_error(result: Any | AppError):
        if isinstance(result, AppError):
            result.raise_error()
        return result

    def raise_error(self):
        raise HTTPException(
            status_code=self.status_code,
            detail={"code": self.code, "message": self.message},
        )


class Errors:
    """Каталог всех доменных ошибок сервиса"""

    @staticmethod
    def email_already_exists(email: str) -> AppError:
        return AppError(
            http.HTTPStatus.BAD_REQUEST, "BAD_REQUEST", f"Email {email} already exists"
        )

    @staticmethod
    def user_not_found() -> AppError:
        return AppError(
            http.HTTPStatus.NOT_FOUND,
            "NOT FOUND",
            "User with such credentials does not exists",
        )

    @staticmethod
    def account_locked(locked_until: datetime) -> AppError:
        return AppError(
            http.HTTPStatus.BAD_REQUEST,
            "BAD_REQUEST",
            f"Account is locked until {locked_until}",
        )

    @staticmethod
    def invalid_credentials() -> AppError:
        return AppError(
            http.HTTPStatus.BAD_REQUEST, "BAD_REQUEST", "Invalid credentials"
        )

    @staticmethod
    def too_many_requests(window: int) -> AppError:
        return AppError(
            http.HTTPStatus.TOO_MANY_REQUESTS,
            "TOO_MANY_REQUESTS",
            f"Too many requests, retry after: {window}",
        )
