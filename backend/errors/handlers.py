"""Error handlers for the autonomous agent system."""

import traceback
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import structlog

from .exceptions import AgentError, ToolExecutionError, LLMServiceError

logger = structlog.get_logger()


class ErrorHandler:
    """Centralized error handling for the agent system."""
    
    @staticmethod
    async def handle_agent_error(
        request: Request, 
        exc: AgentError
    ) -> JSONResponse:
        """Handle AgentError exceptions."""
        
        logger.error(
            "Agent error occurred",
            error_type=exc.__class__.__name__,
            message=exc.message,
            error_code=exc.error_code,
            context=exc.context,
            path=str(request.url),
            method=request.method
        )
        
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "type": exc.__class__.__name__,
                    "message": exc.message,
                    "code": exc.error_code,
                    "context": exc.context
                }
            }
        )
    
    @staticmethod
    async def handle_tool_execution_error(
        request: Request, 
        exc: ToolExecutionError
    ) -> JSONResponse:
        """Handle tool execution errors with specific context."""
        
        logger.error(
            "Tool execution failed",
            tool_name=exc.tool_name,
            tool_args=exc.tool_args,
            message=exc.message,
            original_error=str(exc.original_error) if exc.original_error else None,
            path=str(request.url)
        )
        
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "type": "ToolExecutionError",
                    "message": exc.message,
                    "tool_name": exc.tool_name,
                    "tool_args": exc.tool_args
                }
            }
        )
    
    @staticmethod
    async def handle_llm_service_error(
        request: Request, 
        exc: LLMServiceError
    ) -> JSONResponse:
        """Handle LLM service errors."""
        
        logger.error(
            "LLM service error",
            service=exc.context.get("service"),
            model=exc.context.get("model"),
            status_code=exc.context.get("status_code"),
            message=exc.message,
            path=str(request.url)
        )
        
        status_code = exc.context.get("status_code", 503)
        
        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "type": "LLMServiceError",
                    "message": "LLM service temporarily unavailable",
                    "service": exc.context.get("service"),
                    "retry_after": 30
                }
            }
        )
    
    @staticmethod
    async def handle_general_exception(
        request: Request, 
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions."""
        
        logger.error(
            "Unexpected error occurred",
            error_type=exc.__class__.__name__,
            message=str(exc),
            path=str(request.url),
            method=request.method,
            traceback=traceback.format_exc()
        )
        
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "type": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "request_id": getattr(request.state, "request_id", None)
                }
            }
        )


def setup_error_handlers(app):
    """Set up error handlers for the FastAPI application."""
    
    app.add_exception_handler(AgentError, ErrorHandler.handle_agent_error)
    app.add_exception_handler(ToolExecutionError, ErrorHandler.handle_tool_execution_error)
    app.add_exception_handler(LLMServiceError, ErrorHandler.handle_llm_service_error)
    app.add_exception_handler(Exception, ErrorHandler.handle_general_exception)
    
    logger.info("Error handlers configured successfully")