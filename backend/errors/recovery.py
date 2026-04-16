"""Error recovery strategies for the autonomous agent system."""

import asyncio
import time
from typing import Callable, Any, Optional, Dict
from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import structlog

from .exceptions import ToolExecutionError, LLMServiceError

logger = structlog.get_logger()


class RecoveryStrategy(ABC):
    """Abstract base class for error recovery strategies."""
    
    @abstractmethod
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from the given error."""
        pass


class RetryStrategy(RecoveryStrategy):
    """Retry-based recovery strategy with exponential backoff."""
    
    def __init__(
        self, 
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 10.0,
        exponential_base: int = 2
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
    
    async def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Attempt recovery through retries."""
        operation = context.get("operation")
        
        if not operation:
            raise ValueError("Operation function required in context for retry strategy")
        
        @retry(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(
                multiplier=self.initial_delay,
                min=self.initial_delay,
                max=self.max_delay,
                exp_base=self.exponential_base
            ),
            retry=retry_if_exception_type((ToolExecutionError, LLMServiceError))
        )
        async def retry_operation():
            return await operation()
        
        try:
            result = await retry_operation()
            logger.info(
                "Recovery successful after retry",
                original_error=str(error),
                max_attempts=self.max_attempts
            )
            return result
        except Exception as final_error:
            logger.error(
                "Recovery failed after all retry attempts",
                original_error=str(error),
                final_error=str(final_error),
                max_attempts=self.max_attempts
            )
            raise final_error


class CircuitBreaker:
    """Circuit breaker pattern implementation for failing operations."""
    
    def __init__(
        self, 
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, operation: Callable, *args, **kwargs) -> Any:
        """Execute operation through circuit breaker."""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker moving to HALF_OPEN state")
            else:
                raise Exception(f"Circuit breaker is OPEN. Failing fast.")
        
        try:
            result = await operation(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return True
        
        return time.time() - self.last_failure_time >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful operation."""
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED state")
        
        self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                "Circuit breaker opened due to failures",
                failure_count=self.failure_count,
                threshold=self.failure_threshold
            )


class GracefulDegradation:
    """Implement graceful degradation when services fail."""
    
    @staticmethod
    async def fallback_to_simple_response(error: Exception, context: Dict[str, Any]) -> str:
        """Provide a simple fallback response when AI services fail."""
        
        logger.warning(
            "Falling back to simple response due to error",
            error=str(error),
            context=context
        )
        
        return "I'm experiencing some technical difficulties. Please try again in a moment."
    
    @staticmethod
    async def fallback_to_cached_result(error: Exception, context: Dict[str, Any]) -> Any:
        """Return cached result if available."""
        
        cache = context.get("cache")
        cache_key = context.get("cache_key")
        
        if cache and cache_key:
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info(
                    "Using cached result as fallback",
                    cache_key=cache_key,
                    error=str(error)
                )
                return cached_result
        
        logger.warning(
            "No cached result available for fallback",
            cache_key=cache_key,
            error=str(error)
        )
        
        raise error