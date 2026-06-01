"""Security module — placeholder for future authentication and authorization."""
from core.security.rate_limit import limiter, rate_limit_exceeded_handler

__all__ = ["limiter", "rate_limit_exceeded_handler"]
