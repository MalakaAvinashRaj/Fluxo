"""Base classes for the tool system."""

import time
import uuid
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pydantic import BaseModel, Field
import structlog

from errors.exceptions import ToolExecutionError

logger = structlog.get_logger()


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time": self.execution_time,
            "metadata": self.metadata or {}
        }


class ToolError(Exception):
    """Base exception for tool-related errors."""
    
    def __init__(self, message: str, tool_name: str, original_error: Optional[Exception] = None):
        super().__init__(message)
        self.message = message
        self.tool_name = tool_name
        self.original_error = original_error


class ToolSchema(BaseModel):
    """Schema definition for a tool."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(..., description="JSON schema for tool parameters")
    required: List[str] = Field(default_factory=list, description="List of required parameters")
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI function calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required
                }
            }
        }
    
    def to_anthropic_format(self) -> Dict[str, Any]:
        """Convert to Anthropic tool format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": self.parameters,
                "required": self.required
            }
        }


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self._execution_count = 0
        self._total_execution_time = 0.0
        
    @property
    @abstractmethod
    def schema(self) -> ToolSchema:
        """Return the tool's schema definition."""
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters."""
        pass
    
    async def _execute_with_timing(self, execution_id: str, **kwargs) -> ToolResult:
        """Execute tool with timing and logging."""
        
        start_time = time.time()
        
        logger.info(
            "Tool execution started",
            tool_name=self.name,
            execution_id=execution_id,
            parameters=kwargs
        )
        
        try:
            result = await self.execute(**kwargs)
            execution_time = time.time() - start_time
            
            # Update statistics
            self._execution_count += 1
            self._total_execution_time += execution_time
            
            # Add execution time to result
            result.execution_time = execution_time
            
            logger.info(
                "Tool execution completed successfully",
                tool_name=self.name,
                execution_id=execution_id,
                execution_time=execution_time,
                success=result.success
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.error(
                "Tool execution failed",
                tool_name=self.name,
                execution_id=execution_id,
                execution_time=execution_time,
                error=str(e),
                exc_info=True
            )
            
            # Return error result instead of raising
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                execution_time=execution_time,
                metadata={"error_type": e.__class__.__name__}
            )
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tool parameters against schema."""
        
        try:
            # Check required parameters
            for required_param in self.schema.required:
                if required_param not in parameters:
                    raise ValueError(f"Required parameter '{required_param}' is missing")
            
            # Basic type validation could be added here
            # For now, return parameters as-is
            return parameters
            
        except Exception as e:
            logger.error(
                "Parameter validation failed",
                tool_name=self.name,
                parameters=parameters,
                error=str(e)
            )
            raise ToolExecutionError(
                f"Parameter validation failed for {self.name}: {e}",
                tool_name=self.name,
                tool_args=parameters,
                original_error=e
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tool execution statistics."""
        
        avg_execution_time = (
            self._total_execution_time / self._execution_count 
            if self._execution_count > 0 else 0
        )
        
        return {
            "tool_name": self.name,
            "execution_count": self._execution_count,
            "total_execution_time": self._total_execution_time,
            "average_execution_time": avg_execution_time
        }
    
    async def __call__(self, **kwargs) -> ToolResult:
        """Make tool callable."""
        
        execution_id = str(uuid.uuid4())
        
        # Validate parameters
        validated_params = self.validate_parameters(kwargs)
        
        # Execute with timing
        return await self._execute_with_timing(execution_id, **validated_params)


class SyncToolWrapper(BaseTool):
    """Wrapper to make synchronous tools work with async interface."""
    
    def __init__(self, sync_tool_func, name: str, description: str, schema: ToolSchema):
        super().__init__(name, description)
        self.sync_tool_func = sync_tool_func
        self._schema = schema
    
    @property
    def schema(self) -> ToolSchema:
        return self._schema
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute synchronous tool in thread pool."""
        
        import asyncio
        
        try:
            # Run sync function in thread pool
            result = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.sync_tool_func(**kwargs)
            )
            
            return ToolResult(success=True, data=result)
            
        except Exception as e:
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={"error_type": e.__class__.__name__}
            )