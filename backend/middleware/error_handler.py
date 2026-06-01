"""Global exception handling middleware."""

from __future__ import annotations

import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions with a user-friendly response."""
    request_id = getattr(request.state, "request_id", None)
    logger.error("Unhandled error request_id=%s: %s", request_id, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "SERVER_ERROR",
            "message": "Lỗi server nội bộ. Vui lòng thử lại.",
            "request_id": request_id,
        },
    )
