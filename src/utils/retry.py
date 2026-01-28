"""
Retry Logic with Exponential Backoff

This module provides decorators and utilities for retrying failed operations
with exponential backoff and jitter.
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, TypeVar, ParamSpec, Type

from src.core.exceptions import (
    PlayerIdentificationError,
    RateLimitError,
    TimeoutError,
    WebSearchError,
    ImageDownloadError
)

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')

# Default retryable exceptions
DEFAULT_RETRYABLE_EXCEPTIONS = (
    RateLimitError,
    TimeoutError,
    WebSearchError,
    ImageDownloadError,
    ConnectionError,
    IOError,
)


def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """Decorator to retry function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (including first try)
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff (delay *= base)
        jitter: Add random jitter to delay to prevent thundering herd
        retryable_exceptions: Tuple of exception types that trigger retry
    
    Returns:
        Decorated function that retries on failure
    
    Example:
        @retry_with_backoff(max_attempts=3, initial_delay=1.0)
        def download_image(url: str) -> bytes:
            response = requests.get(url)
            response.raise_for_status()
            return response.content
    """
    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception = None
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    
                    # Add jitter to prevent thundering herd
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )
                    
                    time.sleep(actual_delay)
                    delay *= exponential_base
                
                except Exception as e:
                    # Non-retryable exception - fail immediately
                    logger.error(f"{func.__name__} failed with non-retryable exception: {e}")
                    raise
            
            # Should never reach here, but just in case
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed unexpectedly")
        
        return wrapper
    return decorator


def retry_async_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 10.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[Type[Exception], ...] = DEFAULT_RETRYABLE_EXCEPTIONS
):
    """Decorator to retry async function with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts (including first try)
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        exponential_base: Base for exponential backoff
        jitter: Add random jitter to delay
        retryable_exceptions: Tuple of exception types that trigger retry
    
    Returns:
        Decorated async function that retries on failure
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            import asyncio
            
            last_exception = None
            delay = initial_delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_attempts:
                        logger.error(
                            f"{func.__name__} failed after {max_attempts} attempts: {e}"
                        )
                        raise
                    
                    # Calculate delay with exponential backoff
                    actual_delay = min(delay, max_delay)
                    
                    # Add jitter
                    if jitter:
                        actual_delay *= (0.5 + random.random())
                    
                    logger.warning(
                        f"{func.__name__} attempt {attempt}/{max_attempts} failed: {e}. "
                        f"Retrying in {actual_delay:.2f}s..."
                    )
                    
                    await asyncio.sleep(actual_delay)
                    delay *= exponential_base
                
                except Exception as e:
                    logger.error(f"{func.__name__} failed with non-retryable exception: {e}")
                    raise
            
            if last_exception:
                raise last_exception
            raise RuntimeError(f"{func.__name__} failed unexpectedly")
        
        return wrapper
    return decorator


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: float = 2.0,
        jitter: bool = True
    ):
        """Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            exponential_base: Base for exponential backoff
            jitter: Add random jitter to delay
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
    
    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number.
        
        Args:
            attempt: Attempt number (1-indexed)
        
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.exponential_base ** (attempt - 1))
        delay = min(delay, self.max_delay)
        
        if self.jitter:
            delay *= (0.5 + random.random())
        
        return delay


if __name__ == "__main__":
    # Test retry decorator
    import requests
    
    @retry_with_backoff(max_attempts=3, initial_delay=0.5)
    def flaky_function(fail_count: int = 2):
        """Test function that fails N times before succeeding."""
        if not hasattr(flaky_function, 'attempt'):
            flaky_function.attempt = 0
        
        flaky_function.attempt += 1
        print(f"Attempt {flaky_function.attempt}")
        
        if flaky_function.attempt <= fail_count:
            raise RateLimitError("Rate limit exceeded (test)")
        
        return "Success!"
    
    try:
        result = flaky_function(fail_count=2)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Failed: {e}")
