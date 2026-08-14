from logging import Logger
from typing import override
import uuid

from fastapi import Request, Response
import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from structlog.stdlib import BoundLogger

logger: BoundLogger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    @override
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = str(uuid.uuid7())

        context_logger = logger.bind(request_id=request_id, path=request.url.path)
        request.state.logger = context_logger

        response = await call_next(request)
        context_logger.info("request_completed", status_code=response.status_code)

        return response
