"""Performance metrics collection for the autonomous agent system."""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from contextlib import asynccontextmanager
from prometheus_client import Counter, Histogram, Gauge, start_http_server
import structlog

logger = structlog.get_logger()


class MetricsCollector:
    """Centralized metrics collection for the agent system."""
    
    def __init__(self):
        # Request metrics
        self.request_count = Counter(
            'agent_requests_total', 
            'Total number of requests',
            ['method', 'endpoint', 'status']
        )
        
        self.request_duration = Histogram(
            'agent_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )
        
        # Tool execution metrics
        self.tool_executions = Counter(
            'agent_tool_executions_total',
            'Total number of tool executions',
            ['tool_name', 'status']
        )
        
        self.tool_duration = Histogram(
            'agent_tool_duration_seconds',
            'Tool execution duration in seconds',
            ['tool_name']
        )
        
        # LLM metrics
        self.llm_requests = Counter(
            'agent_llm_requests_total',
            'Total number of LLM requests',
            ['service', 'model', 'status']
        )
        
        self.llm_tokens = Histogram(
            'agent_llm_tokens',
            'Number of tokens in LLM requests',
            ['service', 'model', 'type']  # type: prompt, completion
        )
        
        # System metrics
        self.active_sessions = Gauge(
            'agent_active_sessions',
            'Number of active sessions'
        )
        
        self.memory_usage = Gauge(
            'agent_memory_usage_bytes',
            'Memory usage in bytes',
            ['component']
        )
        
        # Error metrics
        self.errors = Counter(
            'agent_errors_total',
            'Total number of errors',
            ['error_type', 'component']
        )
        
    def record_request(
        self, 
        method: str, 
        endpoint: str, 
        status: int,
        duration: float
    ) -> None:
        """Record HTTP request metrics."""
        
        self.request_count.labels(
            method=method,
            endpoint=endpoint, 
            status=str(status)
        ).inc()
        
        self.request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)
        
    def record_tool_execution(
        self, 
        tool_name: str, 
        status: str,
        duration: float
    ) -> None:
        """Record tool execution metrics."""
        
        self.tool_executions.labels(
            tool_name=tool_name,
            status=status
        ).inc()
        
        self.tool_duration.labels(
            tool_name=tool_name
        ).observe(duration)
        
    def record_llm_request(
        self, 
        service: str, 
        model: str, 
        status: str,
        prompt_tokens: int,
        completion_tokens: int
    ) -> None:
        """Record LLM request metrics."""
        
        self.llm_requests.labels(
            service=service,
            model=model,
            status=status
        ).inc()
        
        self.llm_tokens.labels(
            service=service,
            model=model,
            type='prompt'
        ).observe(prompt_tokens)
        
        self.llm_tokens.labels(
            service=service,
            model=model,
            type='completion'
        ).observe(completion_tokens)
        
    def record_error(self, error_type: str, component: str) -> None:
        """Record error occurrence."""
        
        self.errors.labels(
            error_type=error_type,
            component=component
        ).inc()
        
    def update_active_sessions(self, count: int) -> None:
        """Update active sessions gauge."""
        self.active_sessions.set(count)
        
    def update_memory_usage(self, component: str, bytes_used: int) -> None:
        """Update memory usage gauge."""
        self.memory_usage.labels(component=component).set(bytes_used)


# Global metrics collector instance
metrics = MetricsCollector()


@asynccontextmanager
async def performance_timer(operation_name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for timing operations."""
    
    start_time = time.time()
    labels = labels or {}
    
    logger.debug(
        "Operation started",
        operation=operation_name,
        **labels
    )
    
    try:
        yield
        duration = time.time() - start_time
        
        logger.info(
            "Operation completed successfully",
            operation=operation_name,
            duration_seconds=duration,
            **labels
        )
        
    except Exception as e:
        duration = time.time() - start_time
        
        logger.error(
            "Operation failed",
            operation=operation_name,
            duration_seconds=duration,
            error=str(e),
            **labels
        )
        
        # Record error metric
        metrics.record_error(
            error_type=e.__class__.__name__,
            component=operation_name
        )
        
        raise


def time_function(operation_name: Optional[str] = None):
    """Decorator for timing function execution."""
    
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            
            async with performance_timer(name):
                return await func(*args, **kwargs)
                
        def sync_wrapper(*args, **kwargs):
            name = operation_name or func.__name__
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(
                    "Function executed successfully",
                    function=name,
                    duration_seconds=duration
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                logger.error(
                    "Function execution failed",
                    function=name,
                    duration_seconds=duration,
                    error=str(e)
                )
                
                metrics.record_error(
                    error_type=e.__class__.__name__,
                    component=name
                )
                
                raise
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
            
    return decorator


def start_metrics_server(port: int = 8082) -> None:
    """Start Prometheus metrics HTTP server."""
    
    try:
        start_http_server(port)
        logger.info(
            "Metrics server started",
            port=port,
            endpoint=f"http://localhost:{port}/metrics"
        )
    except Exception as e:
        logger.error(
            "Failed to start metrics server",
            port=port,
            error=str(e)
        )