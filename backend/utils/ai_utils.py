import asyncio
import logging
import random
from typing import Callable, Any

_LOGGER = logging.getLogger(__name__)

async def retry_with_backoff(
    func: Callable, 
    *args, 
    max_retries: int = 5, 
    initial_delay: float = 2.0, 
    exponential_base: float = 2.0,
    jitter: bool = True,
    **kwargs
) -> Any:
    """Retry an async or sync function with exponential backoff."""
    retries = 0
    delay = initial_delay

    while retries <= max_retries:
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                # For sync functions that might be called in a thread
                return func(*args, **kwargs)
        except Exception as e:
            error_str = str(e).lower()
            # Check if it's a rate limit error (429) or overloaded (503)
            is_rate_limit = "429" in error_str or "quota" in error_str or "rate limit" in error_str
            is_overloaded = "503" in error_str or "overloaded" in error_str
            
            if (is_rate_limit or is_overloaded) and retries < max_retries:
                retries += 1
                current_delay = delay * (exponential_base ** (retries - 1))
                if jitter:
                    current_delay += random.uniform(0, 1)
                
                _LOGGER.warning(
                    f"AI Rate limit/overload hit. Retrying in {current_delay:.2f}s... "
                    f"(Attempt {retries}/{max_retries}). Error: {e}"
                )
                await asyncio.sleep(current_delay)
            else:
                _LOGGER.error(f"AI call failed after {retries} retries or non-retryable error: {e}")
                raise e
    return None
