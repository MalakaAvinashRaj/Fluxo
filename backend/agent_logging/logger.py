"""Main logger configuration for the autonomous agent system."""

import sys
import logging
from typing import Optional
import structlog
from config import settings


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None
) -> None:
    """Configure structured logging for the application."""
    
    level = log_level or settings.log_level
    format_type = log_format or settings.log_format
    file_path = log_file or settings.log_file
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        stream=sys.stdout,
        format="%(message)s"
    )
    
    # Configure processors based on format type
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer()
    ]
    
    if format_type.lower() == "json":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())
    
    # Configure structlog
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Set up file logging if specified
    if file_path:
        file_handler = logging.FileHandler(file_path)
        file_handler.setLevel(getattr(logging, level.upper()))
        
        if format_type.lower() == "json":
            file_handler.setFormatter(
                logging.Formatter('%(message)s')
            )
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        # Add file handler to root logger
        logging.getLogger().addHandler(file_handler)
    
    # Create initial log entry
    logger = get_logger()
    logger.info(
        "Logging system initialized",
        log_level=level,
        log_format=format_type,
        log_file=file_path
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured logger instance."""
    
    if name:
        return structlog.get_logger(name)
    else:
        return structlog.get_logger()


class RequestLogger:
    """Logger for HTTP requests with correlation IDs."""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger()
    
    def log_request(
        self, 
        method: str, 
        path: str, 
        request_id: str,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Log incoming HTTP request."""
        
        self.logger.info(
            "HTTP request received",
            method=method,
            path=path,
            request_id=request_id,
            user_agent=user_agent,
            ip_address=ip_address
        )
    
    def log_response(
        self, 
        method: str, 
        path: str, 
        request_id: str,
        status_code: int,
        response_time_ms: float,
        response_size: Optional[int] = None
    ) -> None:
        """Log HTTP response."""
        
        self.logger.info(
            "HTTP response sent",
            method=method,
            path=path,
            request_id=request_id,
            status_code=status_code,
            response_time_ms=response_time_ms,
            response_size=response_size
        )


class ToolLogger:
    """Logger for tool execution with performance metrics."""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger()
    
    def log_tool_start(
        self, 
        tool_name: str, 
        tool_args: dict,
        session_id: str,
        execution_id: str
    ) -> None:
        """Log tool execution start."""
        
        self.logger.info(
            "Tool execution started",
            tool_name=tool_name,
            tool_args=tool_args,
            session_id=session_id,
            execution_id=execution_id
        )
    
    def log_tool_success(
        self, 
        tool_name: str, 
        execution_id: str,
        execution_time_ms: float,
        result_size: Optional[int] = None
    ) -> None:
        """Log successful tool execution."""
        
        self.logger.info(
            "Tool execution completed successfully",
            tool_name=tool_name,
            execution_id=execution_id,
            execution_time_ms=execution_time_ms,
            result_size=result_size
        )
    
    def log_tool_error(
        self, 
        tool_name: str, 
        execution_id: str,
        error: str,
        execution_time_ms: float
    ) -> None:
        """Log tool execution error."""
        
        self.logger.error(
            "Tool execution failed",
            tool_name=tool_name,
            execution_id=execution_id,
            error=error,
            execution_time_ms=execution_time_ms
        )


class SessionLogger:
    """Logger for session-related events."""
    
    def __init__(self, logger: Optional[structlog.BoundLogger] = None):
        self.logger = logger or get_logger()
    
    def log_session_created(self, session_id: str, user_id: Optional[str] = None) -> None:
        """Log session creation."""
        
        self.logger.info(
            "Session created",
            session_id=session_id,
            user_id=user_id
        )
    
    def log_session_ended(
        self, 
        session_id: str, 
        duration_minutes: float,
        tool_calls: int,
        messages_exchanged: int
    ) -> None:
        """Log session end with statistics."""
        
        self.logger.info(
            "Session ended",
            session_id=session_id,
            duration_minutes=duration_minutes,
            tool_calls=tool_calls,
            messages_exchanged=messages_exchanged
        )