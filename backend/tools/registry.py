"""Tool registry for dynamic tool discovery and management."""

from typing import Dict, List, Optional, Type, Any
import importlib
import inspect
from pathlib import Path
import structlog

from .base import BaseTool, ToolSchema
from errors.exceptions import ToolExecutionError

logger = structlog.get_logger()


class ToolRegistry:
    """Registry for managing and discovering tools."""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_schemas: Dict[str, ToolSchema] = {}
        
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool instance."""
        
        try:
            self._tools[tool.name] = tool
            self._tool_schemas[tool.name] = tool.schema
            
            logger.info(
                "Tool registered successfully",
                tool_name=tool.name,
                tool_description=tool.description
            )
            
        except Exception as e:
            logger.error(
                "Failed to register tool",
                tool_name=getattr(tool, 'name', 'unknown'),
                error=str(e),
                exc_info=True
            )
            raise ToolExecutionError(
                f"Failed to register tool: {e}",
                tool_name=getattr(tool, 'name', 'unknown'),
                original_error=e
            )
    
    def register_tool_class(self, tool_class: Type[BaseTool], **kwargs) -> None:
        """Register a tool class by instantiating it."""
        
        try:
            tool_instance = tool_class(**kwargs)
            self.register_tool(tool_instance)
            
        except Exception as e:
            logger.error(
                "Failed to register tool class",
                tool_class=tool_class.__name__,
                error=str(e),
                exc_info=True
            )
            raise ToolExecutionError(
                f"Failed to register tool class {tool_class.__name__}: {e}",
                tool_name=tool_class.__name__,
                original_error=e
            )
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a tool instance by name."""
        
        tool = self._tools.get(tool_name)
        
        if not tool:
            logger.warning(
                "Tool not found in registry",
                tool_name=tool_name,
                available_tools=list(self._tools.keys())
            )
        
        return tool
    
    def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """Get a tool's schema by name."""
        
        return self._tool_schemas.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """Get list of registered tool names."""
        
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> Dict[str, ToolSchema]:
        """Get all tool schemas."""
        
        return self._tool_schemas.copy()
    
    def unregister_tool(self, tool_name: str) -> bool:
        """Unregister a tool."""
        
        if tool_name in self._tools:
            del self._tools[tool_name]
            del self._tool_schemas[tool_name]
            
            logger.info(
                "Tool unregistered successfully",
                tool_name=tool_name
            )
            
            return True
        
        logger.warning(
            "Attempted to unregister non-existent tool",
            tool_name=tool_name
        )
        
        return False
    
    def discover_tools(self, tools_directory: str = "tools") -> None:
        """Discover and register tools from a directory."""
        
        try:
            tools_path = Path(tools_directory)
            
            if not tools_path.exists():
                logger.warning(
                    "Tools directory not found",
                    directory=tools_directory
                )
                return
            
            # Find all Python files in tools directory
            for python_file in tools_path.glob("*.py"):
                if python_file.name.startswith("__"):
                    continue
                
                self._discover_tools_in_module(python_file)
                
            logger.info(
                "Tool discovery completed",
                tools_found=len(self._tools),
                tools_directory=tools_directory
            )
            
        except Exception as e:
            logger.error(
                "Tool discovery failed",
                tools_directory=tools_directory,
                error=str(e),
                exc_info=True
            )
    
    def _discover_tools_in_module(self, module_path: Path) -> None:
        """Discover tools in a specific module."""
        
        try:
            # Import module dynamically
            module_name = module_path.stem
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find BaseTool subclasses
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseTool) and 
                    obj != BaseTool):
                    
                    try:
                        # Try to instantiate the tool
                        tool_instance = obj()
                        self.register_tool(tool_instance)
                        
                        logger.debug(
                            "Tool discovered and registered",
                            tool_name=tool_instance.name,
                            module=module_name
                        )
                        
                    except Exception as e:
                        logger.warning(
                            "Failed to instantiate discovered tool",
                            tool_class=name,
                            module=module_name,
                            error=str(e)
                        )
                        
        except Exception as e:
            logger.error(
                "Failed to discover tools in module",
                module_path=str(module_path),
                error=str(e),
                exc_info=True
            )
    
    def get_tools_for_llm(self, format: str = "openai") -> List[Dict[str, Any]]:
        """Get tool schemas formatted for LLM integration."""
        
        tools = []
        
        for tool_name, schema in self._tool_schemas.items():
            if format.lower() == "openai":
                tools.append(schema.to_openai_format())
            elif format.lower() == "anthropic":
                tools.append(schema.to_anthropic_format())
            else:
                # Default format
                tools.append({
                    "name": schema.name,
                    "description": schema.description,
                    "parameters": schema.parameters,
                    "required": schema.required
                })
        
        return tools
    
    def validate_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """Validate a tool call against its schema."""
        
        tool = self.get_tool(tool_name)
        
        if not tool:
            return False
        
        try:
            tool.validate_parameters(arguments)
            return True
        except Exception:
            return False
    
    def get_tool_statistics(self) -> Dict[str, Dict[str, Any]]:
        """Get execution statistics for all tools."""
        
        stats = {}
        
        for tool_name, tool in self._tools.items():
            stats[tool_name] = tool.get_statistics()
        
        return stats
    
    def clear_registry(self) -> None:
        """Clear all registered tools."""
        
        tool_count = len(self._tools)
        self._tools.clear()
        self._tool_schemas.clear()
        
        logger.info(
            "Tool registry cleared",
            tools_removed=tool_count
        )


# Global tool registry instance
_global_registry: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    
    global _global_registry
    
    if _global_registry is None:
        _global_registry = ToolRegistry()
        
        # Auto-discover and register built-in tools
        _register_builtin_tools(_global_registry)
    
    return _global_registry


def _register_builtin_tools(registry: ToolRegistry) -> None:
    """Register built-in tools."""
    
    try:
        # Import and register built-in tools
        from .file_ops import ReadFileTool, WriteFileTool, SearchFilesTool
        from .command import RunCommandTool
        
        registry.register_tool(ReadFileTool())
        registry.register_tool(WriteFileTool())
        registry.register_tool(SearchFilesTool())
        registry.register_tool(RunCommandTool())
        
        logger.info(
            "Built-in tools registered successfully",
            tool_count=len(registry.list_tools())
        )
        
    except Exception as e:
        logger.error(
            "Failed to register built-in tools",
            error=str(e),
            exc_info=True
        )


def reset_tool_registry() -> None:
    """Reset the global tool registry (mainly for testing)."""
    
    global _global_registry
    _global_registry = None