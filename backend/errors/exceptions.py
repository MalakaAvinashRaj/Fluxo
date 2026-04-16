"""Custom exception classes for the autonomous agent system."""

from typing import Optional, Dict, Any


class AgentError(Exception):
    """Base exception for all agent errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "context": self.context
        }


class ToolExecutionError(AgentError):
    """Error during tool execution."""
    
    def __init__(
        self, 
        message: str, 
        tool_name: Optional[str] = None,
        tool_args: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        context = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "original_error": str(original_error) if original_error else None
        }
        super().__init__(message, "TOOL_EXECUTION_ERROR", context)
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.original_error = original_error


class MemoryError(AgentError):
    """Memory management errors."""
    
    def __init__(
        self, 
        message: str, 
        operation: Optional[str] = None,
        memory_size: Optional[int] = None
    ):
        context = {
            "operation": operation,
            "memory_size": memory_size
        }
        super().__init__(message, "MEMORY_ERROR", context)


class LLMServiceError(AgentError):
    """LLM service communication errors."""
    
    def __init__(
        self, 
        message: str, 
        service: Optional[str] = None,
        model: Optional[str] = None,
        status_code: Optional[int] = None
    ):
        context = {
            "service": service,
            "model": model,
            "status_code": status_code
        }
        super().__init__(message, "LLM_SERVICE_ERROR", context)


class SessionError(AgentError):
    """Session management errors."""
    
    def __init__(
        self, 
        message: str, 
        session_id: Optional[str] = None,
        operation: Optional[str] = None
    ):
        context = {
            "session_id": session_id,
            "operation": operation
        }
        super().__init__(message, "SESSION_ERROR", context)


class ValidationError(AgentError):
    """Data validation errors."""
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None
    ):
        context = {
            "field": field,
            "value": str(value) if value is not None else None
        }
        super().__init__(message, "VALIDATION_ERROR", context)