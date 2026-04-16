"""File operation tools for the autonomous agent system."""

import os
import glob
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import aiofiles
import structlog

from .base import BaseTool, ToolResult, ToolSchema
from errors.exceptions import ToolExecutionError

logger = structlog.get_logger()


class ReadFileTool(BaseTool):
    """Tool for reading file contents."""
    
    def __init__(self):
        super().__init__(
            name="read_file",
            description="Read the contents of a file from the filesystem"
        )
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to read"
                },
                "encoding": {
                    "type": "string", 
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "max_lines": {
                    "type": "integer",
                    "description": "Maximum number of lines to read (optional)",
                    "minimum": 1
                },
                "line_offset": {
                    "type": "integer",
                    "description": "Line number to start reading from (0-indexed, optional)",
                    "minimum": 0
                }
            },
            required=["file_path"]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Read file contents."""
        
        file_path = kwargs.get("file_path")
        encoding = kwargs.get("encoding", "utf-8")
        max_lines = kwargs.get("max_lines")
        line_offset = kwargs.get("line_offset", 0)
        
        try:
            # Resolve path
            path = Path(file_path).resolve()
            
            # Security check - ensure path is within allowed directories
            if not self._is_path_allowed(path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Access denied: Path '{path}' is not in allowed directories"
                )
            
            # Check if file exists
            if not path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"File not found: {path}"
                )
            
            if not path.is_file():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Path is not a file: {path}"
                )
            
            # Read file content
            async with aiofiles.open(path, 'r', encoding=encoding) as f:
                if max_lines or line_offset > 0:
                    # Read with line limits
                    lines = []
                    current_line = 0
                    
                    async for line in f:
                        if current_line < line_offset:
                            current_line += 1
                            continue
                        
                        lines.append(line.rstrip('\n\r'))
                        current_line += 1
                        
                        if max_lines and len(lines) >= max_lines:
                            break
                    
                    content = '\n'.join(lines)
                else:
                    # Read entire file
                    content = await f.read()
            
            # Get file stats
            stat = path.stat()
            
            return ToolResult(
                success=True,
                data={
                    "content": content,
                    "file_path": str(path),
                    "size_bytes": stat.st_size,
                    "lines_read": len(content.split('\n')) if content else 0,
                    "encoding": encoding
                },
                metadata={
                    "operation": "read_file",
                    "file_size": stat.st_size,
                    "line_offset": line_offset,
                    "max_lines": max_lines
                }
            )
            
        except UnicodeDecodeError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Failed to decode file with encoding '{encoding}': {str(e)}"
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Permission denied reading file: {str(e)}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error reading file",
                file_path=file_path,
                error=str(e),
                exc_info=True
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error reading file: {str(e)}"
            )
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        
        # For now, allow all paths within the current working directory and its subdirectories
        # In production, this should be more restrictive
        try:
            cwd = Path.cwd()
            path.resolve().relative_to(cwd.resolve())
            return True
        except ValueError:
            # Path is outside current working directory
            # Allow common system paths for development
            allowed_patterns = [
                "/tmp/",
                "/var/tmp/",
                str(Path.home()),
            ]
            
            path_str = str(path)
            return any(path_str.startswith(pattern) for pattern in allowed_patterns)


class WriteFileTool(BaseTool):
    """Tool for writing content to files."""
    
    def __init__(self):
        super().__init__(
            name="write_file",
            description="Write content to a file on the filesystem"
        )
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "file_path": {
                    "type": "string",
                    "description": "Absolute or relative path to the file to write"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write to the file"
                },
                "encoding": {
                    "type": "string",
                    "description": "File encoding (default: utf-8)",
                    "default": "utf-8"
                },
                "create_directories": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True
                },
                "backup": {
                    "type": "boolean",
                    "description": "Create backup of existing file before overwriting",
                    "default": False
                }
            },
            required=["file_path", "content"]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Write content to file."""
        
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        encoding = kwargs.get("encoding", "utf-8")
        create_directories = kwargs.get("create_directories", True)
        backup = kwargs.get("backup", False)
        
        try:
            # Resolve path
            path = Path(file_path).resolve()
            
            # Security check
            if not self._is_path_allowed(path):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Access denied: Path '{path}' is not in allowed directories"
                )
            
            # Create parent directories if needed
            if create_directories:
                path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create backup if requested and file exists
            backup_path = None
            if backup and path.exists():
                backup_path = path.with_suffix(path.suffix + '.backup')
                backup_path.write_text(path.read_text(encoding=encoding), encoding=encoding)
            
            # Write content to file
            async with aiofiles.open(path, 'w', encoding=encoding) as f:
                await f.write(content)
            
            # Get file stats
            stat = path.stat()
            
            return ToolResult(
                success=True,
                data={
                    "file_path": str(path),
                    "bytes_written": stat.st_size,
                    "lines_written": len(content.split('\n')) if content else 0,
                    "backup_created": backup_path is not None,
                    "backup_path": str(backup_path) if backup_path else None
                },
                metadata={
                    "operation": "write_file",
                    "file_size": stat.st_size,
                    "encoding": encoding,
                    "backup": backup
                }
            )
            
        except PermissionError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Permission denied writing to file: {str(e)}"
            )
        except OSError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"OS error writing file: {str(e)}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error writing file",
                file_path=file_path,
                error=str(e),
                exc_info=True
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error writing file: {str(e)}"
            )
    
    def _is_path_allowed(self, path: Path) -> bool:
        """Check if path is within allowed directories."""
        # Same logic as ReadFileTool
        try:
            cwd = Path.cwd()
            path.resolve().relative_to(cwd.resolve())
            return True
        except ValueError:
            allowed_patterns = [
                "/tmp/",
                "/var/tmp/",
                str(Path.home()),
            ]
            
            path_str = str(path)
            return any(path_str.startswith(pattern) for pattern in allowed_patterns)


class SearchFilesTool(BaseTool):
    """Tool for searching files and content."""
    
    def __init__(self):
        super().__init__(
            name="search_files",
            description="Search for files by name pattern or content"
        )
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "pattern": {
                    "type": "string",
                    "description": "File name pattern to search for (supports glob patterns like *.py, **/*.ts)"
                },
                "search_path": {
                    "type": "string",
                    "description": "Directory to search in (default: current directory)",
                    "default": "."
                },
                "content_pattern": {
                    "type": "string",
                    "description": "Regex pattern to search for within file contents (optional)"
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Whether search should be case sensitive",
                    "default": False
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 100,
                    "minimum": 1,
                    "maximum": 1000
                },
                "include_content": {
                    "type": "boolean",
                    "description": "Include matching lines in results when searching content",
                    "default": True
                }
            },
            required=["pattern"]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Search for files."""
        
        pattern = kwargs.get("pattern")
        search_path = kwargs.get("search_path", ".")
        content_pattern = kwargs.get("content_pattern")
        case_sensitive = kwargs.get("case_sensitive", False)
        max_results = kwargs.get("max_results", 100)
        include_content = kwargs.get("include_content", True)
        
        try:
            # Resolve search path
            base_path = Path(search_path).resolve()
            
            if not base_path.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Search path does not exist: {base_path}"
                )
            
            # Find files by pattern
            matching_files = []
            
            if "**" in pattern:
                # Recursive search
                for file_path in base_path.rglob(pattern):
                    if file_path.is_file() and len(matching_files) < max_results:
                        matching_files.append(file_path)
            else:
                # Non-recursive search
                for file_path in base_path.glob(pattern):
                    if file_path.is_file() and len(matching_files) < max_results:
                        matching_files.append(file_path)
            
            results = []
            
            # Process each matching file
            for file_path in matching_files:
                try:
                    file_info = {
                        "file_path": str(file_path.relative_to(base_path)),
                        "absolute_path": str(file_path),
                        "size_bytes": file_path.stat().st_size,
                        "modified_time": file_path.stat().st_mtime
                    }
                    
                    # Search content if pattern provided
                    if content_pattern:
                        content_matches = await self._search_file_content(
                            file_path, 
                            content_pattern, 
                            case_sensitive,
                            include_content
                        )
                        
                        if content_matches:
                            file_info["content_matches"] = content_matches
                            results.append(file_info)
                    else:
                        # Just file name match
                        results.append(file_info)
                        
                except Exception as e:
                    logger.warning(
                        "Error processing file during search",
                        file_path=str(file_path),
                        error=str(e)
                    )
                    continue
            
            return ToolResult(
                success=True,
                data={
                    "results": results,
                    "total_found": len(results),
                    "search_pattern": pattern,
                    "search_path": str(base_path),
                    "content_search": content_pattern is not None
                },
                metadata={
                    "operation": "search_files",
                    "pattern": pattern,
                    "content_pattern": content_pattern,
                    "results_count": len(results)
                }
            )
            
        except Exception as e:
            logger.error(
                "Unexpected error during file search",
                pattern=pattern,
                search_path=search_path,
                error=str(e),
                exc_info=True
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error during search: {str(e)}"
            )
    
    async def _search_file_content(
        self,
        file_path: Path,
        content_pattern: str,
        case_sensitive: bool,
        include_content: bool
    ) -> List[Dict[str, Any]]:
        """Search for pattern within file content."""
        
        try:
            # Compile regex pattern
            flags = 0 if case_sensitive else re.IGNORECASE
            regex = re.compile(content_pattern, flags)
            
            matches = []
            
            # Read file and search
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_number = 1
                
                async for line in f:
                    if regex.search(line):
                        match_info = {
                            "line_number": line_number,
                            "match_count": len(regex.findall(line))
                        }
                        
                        if include_content:
                            match_info["line_content"] = line.rstrip('\n\r')
                        
                        matches.append(match_info)
                    
                    line_number += 1
            
            return matches
            
        except Exception as e:
            logger.warning(
                "Error searching file content",
                file_path=str(file_path),
                error=str(e)
            )
            return []