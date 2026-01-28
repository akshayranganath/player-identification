"""
Circuit Breaker Pattern

This module implements the circuit breaker pattern to prevent cascading failures
when external services are down or slow.
"""

import time
import logging
from enum import Enum
from typing import Callable, TypeVar, ParamSpec
from functools import wraps
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

P = ParamSpec('P')
T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation, requests pass through
    OPEN = "open"          # Circuit tripped, requests fail fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    last_failure_time: datetime | None = None
    last_success_time: datetime | None = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    """Circuit breaker implementation.
    
    The circuit breaker has three states:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Too many failures, requests fail fast without calling service
    - HALF_OPEN: Testing if service recovered, limited requests allowed
    
    Example:
        breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)
        
        @breaker
        def call_external_api():
            return requests.get("https://api.example.com/data")
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type[Exception] = Exception,
        name: str = "CircuitBreaker"
    ):
        """Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of consecutive failures before opening
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type that counts as failure
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self._state = CircuitState.CLOSED
        self._stats = CircuitBreakerStats()
        self._opened_at: float | None = None
    
    @property
    def state(self) -> CircuitState:
        """Get current circuit state."""
        return self._state
    
    @property
    def stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics."""
        return self._stats
    
    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Decorator to wrap function with circuit breaker.
        
        Args:
            func: Function to wrap
        
        Returns:
            Wrapped function
        """
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return self.call(func, *args, **kwargs)
        return wrapper
    
    def call(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
        """Call function with circuit breaker protection.
        
        Args:
            func: Function to call
            *args: Positional arguments
            **kwargs: Keyword arguments
        
        Returns:
            Function result
        
        Raises:
            Exception: If circuit is open or function fails
        """
        # Check if we should attempt the call
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._transition_to_half_open()
            else:
                raise Exception(
                    f"Circuit breaker '{self.name}' is OPEN. "
                    f"Service unavailable. Retry after {self.recovery_timeout}s."
                )
        
        # Attempt the call
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self._opened_at is None:
            return True
        return time.time() - self._opened_at >= self.recovery_timeout
    
    def _transition_to_half_open(self) -> None:
        """Transition from OPEN to HALF_OPEN state."""
        logger.info(f"Circuit breaker '{self.name}' transitioning to HALF_OPEN")
        self._state = CircuitState.HALF_OPEN
        self._stats.consecutive_failures = 0
        self._stats.consecutive_successes = 0
    
    def _on_success(self) -> None:
        """Handle successful call."""
        self._stats.total_calls += 1
        self._stats.successful_calls += 1
        self._stats.consecutive_successes += 1
        self._stats.consecutive_failures = 0
        self._stats.last_success_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            # Successful test in HALF_OPEN, close the circuit
            logger.info(f"Circuit breaker '{self.name}' closing after successful test")
            self._state = CircuitState.CLOSED
            self._opened_at = None
    
    def _on_failure(self) -> None:
        """Handle failed call."""
        self._stats.total_calls += 1
        self._stats.failed_calls += 1
        self._stats.consecutive_failures += 1
        self._stats.consecutive_successes = 0
        self._stats.last_failure_time = datetime.now()
        
        if self._state == CircuitState.HALF_OPEN:
            # Failed test in HALF_OPEN, open the circuit again
            logger.warning(f"Circuit breaker '{self.name}' opening after failed test")
            self._state = CircuitState.OPEN
            self._opened_at = time.time()
        
        elif self._state == CircuitState.CLOSED:
            # Check if we should open the circuit
            if self._stats.consecutive_failures >= self.failure_threshold:
                logger.error(
                    f"Circuit breaker '{self.name}' opening after "
                    f"{self._stats.consecutive_failures} consecutive failures"
                )
                self._state = CircuitState.OPEN
                self._opened_at = time.time()
    
    def reset(self) -> None:
        """Manually reset circuit breaker to CLOSED state."""
        logger.info(f"Circuit breaker '{self.name}' manually reset")
        self._state = CircuitState.CLOSED
        self._opened_at = None
        self._stats.consecutive_failures = 0
        self._stats.consecutive_successes = 0
    
    def get_status(self) -> dict:
        """Get circuit breaker status.
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "state": self._state.value,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout,
            "stats": {
                "total_calls": self._stats.total_calls,
                "successful_calls": self._stats.successful_calls,
                "failed_calls": self._stats.failed_calls,
                "consecutive_failures": self._stats.consecutive_failures,
                "consecutive_successes": self._stats.consecutive_successes,
                "last_failure": self._stats.last_failure_time.isoformat() if self._stats.last_failure_time else None,
                "last_success": self._stats.last_success_time.isoformat() if self._stats.last_success_time else None,
            }
        }


if __name__ == "__main__":
    # Test circuit breaker
    breaker = CircuitBreaker(
        failure_threshold=3,
        recovery_timeout=2.0,
        name="TestBreaker"
    )
    
    call_count = 0
    
    @breaker
    def flaky_service():
        """Service that fails first 5 times."""
        nonlocal call_count
        call_count += 1
        print(f"Call {call_count}")
        
        if call_count <= 5:
            raise Exception("Service unavailable")
        return "Success!"
    
    # Test circuit breaker behavior
    for i in range(10):
        try:
            result = flaky_service()
            print(f"✓ {result}")
        except Exception as e:
            print(f"✗ {e}")
        
        time.sleep(0.5)
    
    print("\nCircuit Breaker Status:")
    import json
    print(json.dumps(breaker.get_status(), indent=2))
