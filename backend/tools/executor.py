"""Tool execution system with parallel processing capabilities."""

import asyncio
import uuid
from typing import Dict, List, Any, Optional, Tuple
import structlog

from .base import BaseTool, ToolResult
from .registry import ToolRegistry
from errors.exceptions import ToolExecutionError
from agent_logging.metrics import metrics, performance_timer

logger = structlog.get_logger()


class ToolExecutor:
    """Executes individual tools with error handling and metrics."""
    
    def __init__(self, tool_registry: ToolRegistry):
        self.tool_registry = tool_registry
        
    async def execute_tool(
        self, 
        tool_name: str, 
        arguments: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> ToolResult:
        """Execute a single tool."""
        
        execution_id = str(uuid.uuid4())
        
        try:
            # Get tool from registry
            tool = self.tool_registry.get_tool(tool_name)
            if not tool:
                raise ToolExecutionError(
                    f"Tool '{tool_name}' not found",
                    tool_name=tool_name,
                    tool_args=arguments
                )
            
            # Execute tool with timing
            async with performance_timer(
                f"tool_execution_{tool_name}",
                {"tool_name": tool_name, "session_id": session_id}
            ):
                result = await tool(**arguments)
            
            # Record metrics
            status = "success" if result.success else "error"
            metrics.record_tool_execution(
                tool_name=tool_name,
                status=status,
                duration=result.execution_time or 0
            )
            
            logger.info(
                "Tool executed successfully",
                tool_name=tool_name,
                execution_id=execution_id,
                session_id=session_id,
                success=result.success,
                execution_time=result.execution_time
            )
            
            return result
            
        except Exception as e:
            logger.error(
                "Tool execution failed",
                tool_name=tool_name,
                execution_id=execution_id,
                session_id=session_id,
                error=str(e),
                arguments=arguments,
                exc_info=True
            )
            
            # Record error metrics
            metrics.record_tool_execution(
                tool_name=tool_name,
                status="error", 
                duration=0
            )
            
            # Return error result
            return ToolResult(
                success=False,
                data=None,
                error=str(e),
                metadata={
                    "error_type": e.__class__.__name__,
                    "execution_id": execution_id
                }
            )


class ParallelToolExecutor:
    """Executes multiple tools in parallel like Cursor's approach."""
    
    def __init__(self, tool_registry: ToolRegistry, max_concurrent: int = 10):
        self.tool_registry = tool_registry
        self.max_concurrent = max_concurrent
        self.tool_executor = ToolExecutor(tool_registry)
        
    async def execute_tools_parallel(
        self, 
        tool_calls: List[Dict[str, Any]],
        session_id: Optional[str] = None
    ) -> Tuple[Dict[str, ToolResult], Dict[str, str]]:
        """
        Execute multiple tools in parallel with error isolation.
        
        Returns:
            Tuple of (successful_results, errors)
        """
        
        if not tool_calls:
            return {}, {}
        
        logger.info(
            "Starting parallel tool execution",
            tool_count=len(tool_calls),
            session_id=session_id,
            max_concurrent=self.max_concurrent
        )
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def execute_single_tool(tool_spec: Dict[str, Any]) -> Tuple[str, ToolResult]:
            """Execute a single tool with concurrency control."""
            
            async with semaphore:
                tool_name = tool_spec.get("name") or tool_spec.get("function", {}).get("name")
                arguments = tool_spec.get("arguments", {}) or tool_spec.get("function", {}).get("arguments", {})
                call_id = tool_spec.get("id", str(uuid.uuid4()))
                
                if not tool_name:
                    error_result = ToolResult(
                        success=False,
                        data=None,
                        error="Missing tool name in call specification"
                    )
                    return call_id, error_result
                
                try:
                    result = await self.tool_executor.execute_tool(
                        tool_name=tool_name,
                        arguments=arguments,
                        session_id=session_id
                    )
                    
                    return call_id, result
                    
                except Exception as e:
                    logger.error(
                        "Unexpected error in parallel tool execution",
                        tool_name=tool_name,
                        call_id=call_id,
                        error=str(e),
                        exc_info=True
                    )
                    
                    error_result = ToolResult(
                        success=False,
                        data=None,
                        error=f"Unexpected error: {str(e)}",
                        metadata={"error_type": e.__class__.__name__}
                    )
                    
                    return call_id, error_result
        
        # Execute all tools concurrently
        try:
            async with performance_timer(
                "parallel_tool_execution",
                {"tool_count": len(tool_calls), "session_id": session_id}
            ):
                results = await asyncio.gather(
                    *[execute_single_tool(tool_spec) for tool_spec in tool_calls],
                    return_exceptions=True
                )
            
            # Process results
            successful_results = {}
            errors = {}
            
            for i, result_tuple in enumerate(results):
                if isinstance(result_tuple, Exception):
                    # Handle gather exceptions
                    call_id = f"call_{i}"
                    error_msg = f"Task failed with exception: {str(result_tuple)}"
                    errors[call_id] = error_msg
                    
                    logger.error(
                        "Tool execution task failed",
                        call_id=call_id,
                        error=error_msg,
                        tool_spec=tool_calls[i] if i < len(tool_calls) else None
                    )
                    
                else:
                    call_id, tool_result = result_tuple
                    
                    if tool_result.success:
                        successful_results[call_id] = tool_result
                    else:
                        errors[call_id] = tool_result.error or "Unknown error"
            
            logger.info(
                "Parallel tool execution completed",
                total_tools=len(tool_calls),
                successful=len(successful_results),
                failed=len(errors),
                session_id=session_id
            )
            
            return successful_results, errors
            
        except Exception as e:
            logger.error(
                "Critical error in parallel tool execution",
                error=str(e),
                tool_calls=tool_calls,
                session_id=session_id,
                exc_info=True
            )
            
            # Return all as errors
            errors = {f"call_{i}": str(e) for i in range(len(tool_calls))}
            return {}, errors
    
    async def execute_tools_sequential(
        self, 
        tool_calls: List[Dict[str, Any]],
        session_id: Optional[str] = None,
        stop_on_error: bool = False
    ) -> Tuple[Dict[str, ToolResult], Dict[str, str]]:
        """Execute tools sequentially with optional error handling."""
        
        logger.info(
            "Starting sequential tool execution",
            tool_count=len(tool_calls),
            session_id=session_id,
            stop_on_error=stop_on_error
        )
        
        successful_results = {}
        errors = {}
        
        for i, tool_spec in enumerate(tool_calls):
            tool_name = tool_spec.get("name") or tool_spec.get("function", {}).get("name")
            arguments = tool_spec.get("arguments", {}) or tool_spec.get("function", {}).get("arguments", {})
            call_id = tool_spec.get("id", f"call_{i}")
            
            try:
                result = await self.tool_executor.execute_tool(
                    tool_name=tool_name,
                    arguments=arguments,
                    session_id=session_id
                )
                
                if result.success:
                    successful_results[call_id] = result
                else:
                    errors[call_id] = result.error or "Unknown error"
                    
                    if stop_on_error:
                        logger.warning(
                            "Stopping sequential execution due to error",
                            call_id=call_id,
                            error=result.error,
                            completed_tools=len(successful_results)
                        )
                        break
                        
            except Exception as e:
                error_msg = str(e)
                errors[call_id] = error_msg
                
                logger.error(
                    "Sequential tool execution failed",
                    call_id=call_id,
                    tool_name=tool_name,
                    error=error_msg,
                    exc_info=True
                )
                
                if stop_on_error:
                    break
        
        logger.info(
            "Sequential tool execution completed",
            total_tools=len(tool_calls),
            successful=len(successful_results),
            failed=len(errors),
            session_id=session_id
        )
        
        return successful_results, errors
    
    def get_available_tools(self) -> List[Dict[str, Any]]:
        """Get list of available tools with their schemas."""
        
        tools = []
        for tool_name in self.tool_registry.list_tools():
            tool = self.tool_registry.get_tool(tool_name)
            if tool:
                tools.append({
                    "name": tool.name,
                    "description": tool.description,
                    "schema": tool.schema.to_openai_format(),
                    "statistics": tool.get_statistics()
                })
        
        return tools