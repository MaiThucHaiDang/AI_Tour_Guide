"""Shared API rate limiting helpers."""

from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return the same user-facing error shape for limited requests."""
    request_id = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Bạn đang gửi yêu cầu quá nhanh. Vui lòng thử lại sau ít phút.",
            "detail": str(exc.detail),
            "request_id": request_id,
        },
    )
