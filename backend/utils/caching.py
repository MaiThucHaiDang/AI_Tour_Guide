"""Caching utilities for performance optimization."""

from __future__ import annotations

import hashlib
import json
import functools
from typing import Any, Callable, TypeVar
import logging

_LOGGER = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Simple response cache with max size
_RESPONSE_CACHE: dict[str, Any] = {}
_MAX_CACHE_SIZE = 200


def cache_response(func: F) -> F:
    """Decorator to cache function responses based on arguments.
    
    Uses simple dict cache with max size limit. When limit exceeded,
    oldest entries are evicted (FIFO).
    
    Args:
        func: Async function to cache
        
    Returns:
        Wrapped function with caching
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        # Create cache key from function name and arguments
        cache_key = _make_cache_key(func.__name__, args, kwargs)
        
        # Check cache
        if cache_key in _RESPONSE_CACHE:
            _LOGGER.debug("Cache hit for %s", func.__name__)
            return _RESPONSE_CACHE[cache_key]
        
        # Execute function
        result = await func(*args, **kwargs)
        
        # Store in cache with size management
        if len(_RESPONSE_CACHE) >= _MAX_CACHE_SIZE:
            # Remove oldest entry (FIFO)
            oldest_key = next(iter(_RESPONSE_CACHE))
            del _RESPONSE_CACHE[oldest_key]
            _LOGGER.debug("Cache evicted oldest entry")
        
        _RESPONSE_CACHE[cache_key] = result
        _LOGGER.debug("Cache stored for %s", func.__name__)
        
        return result
    
    return wrapper


def _make_cache_key(func_name: str, args: tuple, kwargs: dict) -> str:
    """Generate cache key from function name and arguments.
    
    Converts non-hashable types to string representation.
    """
    # Filter out request objects and unhashable types
    safe_args = []
    for arg in args:
        if hasattr(arg, '__dict__') and 'state' in arg.__dict__:
            # Skip Request objects
            continue
        try:
            hash(arg)
            safe_args.append(arg)
        except TypeError:
            safe_args.append(str(arg)[:50])  # Truncate long strings
    
    # Build key
    key_parts = [func_name] + [str(a) for a in safe_args] + [str(kwargs)]
    key_str = "|".join(key_parts)
    
    # Hash to keep key reasonable size
    return hashlib.md5(key_str.encode()).hexdigest()


def clear_cache() -> None:
    """Clear all cached responses."""
    global _RESPONSE_CACHE
    _RESPONSE_CACHE.clear()
    _LOGGER.info("Response cache cleared")
