"""Command execution tool for the autonomous agent system."""

import asyncio
import os
import shlex
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

from .base import BaseTool, ToolResult, ToolSchema
from config import settings

logger = structlog.get_logger()


class RunCommandTool(BaseTool):
    """Tool for executing shell commands safely."""
    
    def __init__(self):
        super().__init__(
            name="run_command",
            description="Execute shell commands in a controlled environment"
        )
        
        # Define allowed commands for security
        self.allowed_commands = {
            # File operations
            "ls", "cat", "head", "tail", "find", "grep", "wc",
            # Git operations
            "git",
            # Node/npm operations
            "npm", "node", "yarn", "bun",
            # Python operations
            "python", "python3", "pip", "pip3",
            # Build tools
            "make", "cmake", "cargo",
            # System info
            "pwd", "whoami", "which", "echo",
            # File permissions
            "chmod", "chown"
        }
    
    @property
    def schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters={
                "command": {
                    "type": "string",
                    "description": "Command to execute"
                },
                "working_directory": {
                    "type": "string",
                    "description": "Working directory for command execution (default: current directory)",
                    "default": "."
                },
                "timeout": {
                    "type": "integer",
                    "description": "Command timeout in seconds",
                    "default": 30,
                    "minimum": 1,
                    "maximum": 300
                },
                "capture_output": {
                    "type": "boolean",
                    "description": "Capture stdout and stderr",
                    "default": True
                },
                "environment": {
                    "type": "object",
                    "description": "Additional environment variables",
                    "additionalProperties": {"type": "string"}
                }
            },
            required=["command"]
        )
    
    async def execute(self, **kwargs) -> ToolResult:
        """Execute shell command."""
        
        command = kwargs.get("command")
        working_directory = kwargs.get("working_directory", ".")
        timeout = kwargs.get("timeout", settings.tool_timeout)
        capture_output = kwargs.get("capture_output", True)
        environment = kwargs.get("environment", {})
        
        try:
            # Security validation
            if not self._is_command_allowed(command):
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Command not allowed for security reasons: {command}"
                )
            
            # Resolve working directory
            work_dir = Path(working_directory).resolve()
            
            if not work_dir.exists():
                return ToolResult(
                    success=False,
                    data=None,
                    error=f"Working directory does not exist: {work_dir}"
                )
            
            # Prepare environment
            env = os.environ.copy()
            env.update(environment)
            
            # Parse command safely
            if isinstance(command, str):
                # Split command string into arguments
                try:
                    cmd_args = shlex.split(command)
                except ValueError as e:
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Invalid command syntax: {str(e)}"
                    )
            else:
                cmd_args = command
            
            logger.info(
                "Executing command",
                command=command,
                working_directory=str(work_dir),
                timeout=timeout
            )
            
            # Execute command
            if capture_output:
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    cwd=work_dir,
                    env=env,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=timeout
                    )
                    
                    stdout_text = stdout.decode('utf-8', errors='replace')
                    stderr_text = stderr.decode('utf-8', errors='replace')
                    
                except asyncio.TimeoutError:
                    # Kill the process if it times out
                    process.kill()
                    await process.wait()
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Command timed out after {timeout} seconds"
                    )
                
            else:
                # Execute without capturing output
                process = await asyncio.create_subprocess_exec(
                    *cmd_args,
                    cwd=work_dir,
                    env=env
                )
                
                try:
                    await asyncio.wait_for(process.wait(), timeout=timeout)
                    stdout_text = ""
                    stderr_text = ""
                    
                except asyncio.TimeoutError:
                    process.kill()
                    await process.wait()
                    
                    return ToolResult(
                        success=False,
                        data=None,
                        error=f"Command timed out after {timeout} seconds"
                    )
            
            # Determine success based on return code
            success = process.returncode == 0
            
            result_data = {
                "return_code": process.returncode,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command,
                "working_directory": str(work_dir)
            }
            
            if success:
                logger.info(
                    "Command executed successfully",
                    command=command,
                    return_code=process.returncode,
                    stdout_length=len(stdout_text),
                    stderr_length=len(stderr_text)
                )
                
                return ToolResult(
                    success=True,
                    data=result_data,
                    metadata={
                        "operation": "run_command",
                        "return_code": process.returncode,
                        "timeout": timeout
                    }
                )
            else:
                logger.warning(
                    "Command executed with non-zero return code",
                    command=command,
                    return_code=process.returncode,
                    stderr=stderr_text[:500]  # Limit stderr in logs
                )
                
                return ToolResult(
                    success=False,
                    data=result_data,
                    error=f"Command failed with return code {process.returncode}: {stderr_text[:200]}",
                    metadata={
                        "operation": "run_command",
                        "return_code": process.returncode,
                        "timeout": timeout
                    }
                )
                
        except FileNotFoundError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Command not found: {str(e)}"
            )
        except PermissionError as e:
            return ToolResult(
                success=False,
                data=None,
                error=f"Permission denied: {str(e)}"
            )
        except Exception as e:
            logger.error(
                "Unexpected error executing command",
                command=command,
                error=str(e),
                exc_info=True
            )
            return ToolResult(
                success=False,
                data=None,
                error=f"Unexpected error executing command: {str(e)}"
            )
    
    def _is_command_allowed(self, command: str) -> bool:
        """Check if command is allowed for execution."""
        
        try:
            # Parse command to get the base command
            cmd_args = shlex.split(command)
            if not cmd_args:
                return False
            
            base_command = cmd_args[0]
            
            # Remove path components to get just the command name
            command_name = os.path.basename(base_command)
            
            # Check against allowed commands
            if command_name in self.allowed_commands:
                return True
            
            # Check for dangerous commands
            dangerous_commands = {
                "rm", "rmdir", "del", "format", "fdisk",
                "mkfs", "dd", "su", "sudo", "passwd",
                "shutdown", "reboot", "halt", "kill",
                "killall", "pkill", "nc", "netcat",
                "wget", "curl", "ssh", "scp", "ftp"
            }
            
            if command_name in dangerous_commands:
                logger.warning(
                    "Dangerous command blocked",
                    command=command,
                    base_command=command_name
                )
                return False
            
            # Check for shell operators that could be dangerous
            dangerous_operators = [
                "|", ">", ">>", "<", "&&", "||", ";", "`", "$("
            ]
            
            for operator in dangerous_operators:
                if operator in command:
                    logger.warning(
                        "Command with dangerous operator blocked",
                        command=command,
                        operator=operator
                    )
                    return False
            
            # For unknown commands, be cautious
            logger.warning(
                "Unknown command - blocking for security",
                command=command,
                base_command=command_name
            )
            return False
            
        except Exception as e:
            logger.error(
                "Error validating command",
                command=command,
                error=str(e)
            )
            return False
    
    def add_allowed_command(self, command: str) -> None:
        """Add a command to the allowed list."""
        self.allowed_commands.add(command)
        logger.info(
            "Command added to allowed list",
            command=command
        )
    
    def remove_allowed_command(self, command: str) -> None:
        """Remove a command from the allowed list."""
        self.allowed_commands.discard(command)
        logger.info(
            "Command removed from allowed list",
            command=command
        )
    
    def get_allowed_commands(self) -> List[str]:
        """Get list of allowed commands."""
        return list(self.allowed_commands)