"""Task execution and autonomous pipeline for the agent system."""

import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import structlog

from config import settings
from memory import MemoryManager
from tools import ParallelToolExecutor
from services.llm_service import LLMService
from errors.exceptions import AgentError
from agent_logging.metrics import performance_timer

logger = structlog.get_logger()


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskStep:
    """Represents a single step in a task."""
    id: str
    description: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time: Optional[float] = None


@dataclass
class Task:
    """Represents an autonomous task with multiple steps."""
    id: str
    title: str
    description: str
    steps: List[TaskStep] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskExecutor:
    """Executes individual task steps."""
    
    def __init__(
        self,
        tool_executor: ParallelToolExecutor,
        llm_service: LLMService,
        memory: MemoryManager
    ):
        self.tool_executor = tool_executor
        self.llm_service = llm_service
        self.memory = memory
    
    async def execute_step(
        self,
        step: TaskStep,
        session_id: str
    ) -> TaskStep:
        """Execute a single task step."""
        
        step.status = TaskStatus.RUNNING
        step.started_at = datetime.utcnow()
        
        logger.info(
            "Task step started",
            step_id=step.id,
            description=step.description,
            session_id=session_id,
            tool_count=len(step.tool_calls)
        )
        
        try:
            async with performance_timer(
                f"task_step_{step.id}",
                {"session_id": session_id, "step_id": step.id}
            ):
                if step.tool_calls:
                    # Execute tools for this step
                    successful_results, errors = await self.tool_executor.execute_tools_parallel(
                        step.tool_calls,
                        session_id=session_id
                    )
                    
                    if errors:
                        # Some tools failed
                        error_msg = f"Tool execution failed: {list(errors.values())}"
                        step.status = TaskStatus.FAILED
                        step.error = error_msg
                        
                        logger.error(
                            "Task step failed due to tool errors",
                            step_id=step.id,
                            errors=errors,
                            session_id=session_id
                        )
                    else:
                        # All tools succeeded
                        step.status = TaskStatus.COMPLETED
                        step.result = successful_results
                        
                        logger.info(
                            "Task step completed successfully",
                            step_id=step.id,
                            session_id=session_id,
                            results_count=len(successful_results)
                        )
                else:
                    # No tools to execute - just mark as completed
                    step.status = TaskStatus.COMPLETED
                    step.result = {"message": "Step completed without tool execution"}
            
            step.completed_at = datetime.utcnow()
            if step.started_at:
                step.execution_time = (step.completed_at - step.started_at).total_seconds()
            
        except Exception as e:
            step.status = TaskStatus.FAILED
            step.error = str(e)
            step.completed_at = datetime.utcnow()
            
            logger.error(
                "Task step execution failed",
                step_id=step.id,
                session_id=session_id,
                error=str(e),
                exc_info=True
            )
        
        return step


class AutonomousTaskExecutor:
    """Executes autonomous tasks with planning and adaptation."""
    
    def __init__(
        self,
        tool_executor: ParallelToolExecutor,
        llm_service: LLMService,
        memory: MemoryManager,
        session_id: str
    ):
        self.tool_executor = tool_executor
        self.llm_service = llm_service
        self.memory = memory
        self.session_id = session_id
        self.task_executor = TaskExecutor(tool_executor, llm_service, memory)
        
        # Current task state
        self.current_task: Optional[Task] = None
        self.is_executing = False
    
    async def create_task_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Task:
        """Create an autonomous task plan from user request."""
        
        logger.info(
            "Creating task plan",
            user_request=user_request[:100],
            session_id=self.session_id
        )
        
        # Get available tools
        available_tools = self.tool_executor.get_available_tools()
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}" 
            for tool in available_tools
        ])
        
        # Create planning prompt
        planning_prompt = f"""
You are an autonomous AI agent that creates detailed task plans. Given a user request, break it down into specific, executable steps using the available tools.

Available Tools:
{tools_description}

User Request: {user_request}

Create a detailed task plan with the following JSON structure:
{{
    "title": "Brief task title",
    "description": "Detailed description of what needs to be done",
    "steps": [
        {{
            "id": "step_1",
            "description": "What this step accomplishes",
            "tool_calls": [
                {{
                    "name": "tool_name",
                    "arguments": {{"param": "value"}}
                }}
            ]
        }}
    ]
}}

Guidelines:
1. Break complex tasks into smaller, manageable steps
2. Each step should have a clear purpose and outcome
3. Use appropriate tools for each step
4. Consider dependencies between steps
5. Be specific with tool parameters
6. Ensure steps are executable and measurable

Focus on creating actionable steps that can be executed autonomously.
"""
        
        try:
            # Get conversation history for context
            messages = await self.memory.get_conversation_history()
            
            # Add planning prompt
            planning_messages = messages + [{
                "role": "user",
                "content": planning_prompt
            }]
            
            # Get plan from LLM
            response = await self.llm_service.complete_chat(
                messages=planning_messages,
                temperature=0.1  # Lower temperature for more consistent planning
            )
            
            # Parse the response to extract task plan
            plan_content = response.get("content", "")
            
            # Try to extract JSON from the response
            import json
            import re
            
            # Look for JSON in the response
            json_match = re.search(r'\{.*\}', plan_content, re.DOTALL)
            if json_match:
                plan_data = json.loads(json_match.group())
            else:
                # Fallback: create a simple plan
                plan_data = {
                    "title": "User Request",
                    "description": user_request,
                    "steps": [{
                        "id": "step_1",
                        "description": f"Execute user request: {user_request}",
                        "tool_calls": []
                    }]
                }
            
            # Create task object
            task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            task = Task(
                id=task_id,
                title=plan_data.get("title", "Autonomous Task"),
                description=plan_data.get("description", user_request),
                metadata={
                    "user_request": user_request,
                    "context": context,
                    "llm_response": plan_content
                }
            )
            
            # Create task steps
            for i, step_data in enumerate(plan_data.get("steps", [])):
                step = TaskStep(
                    id=step_data.get("id", f"step_{i+1}"),
                    description=step_data.get("description", f"Step {i+1}"),
                    tool_calls=step_data.get("tool_calls", [])
                )
                task.steps.append(step)
            
            logger.info(
                "Task plan created",
                task_id=task.id,
                title=task.title,
                steps_count=len(task.steps),
                session_id=self.session_id
            )
            
            return task
            
        except Exception as e:
            logger.error(
                "Failed to create task plan",
                user_request=user_request,
                session_id=self.session_id,
                error=str(e),
                exc_info=True
            )
            
            # Create fallback task
            task_id = f"task_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            return Task(
                id=task_id,
                title="Fallback Task",
                description=f"Process user request: {user_request}",
                steps=[
                    TaskStep(
                        id="step_1",
                        description=f"Handle request: {user_request}",
                        tool_calls=[]
                    )
                ]
            )
    
    async def execute_task(
        self,
        task: Task,
        adaptive: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute an autonomous task with optional adaptation."""
        
        if self.is_executing:
            raise AgentError("Task executor is already running")
        
        self.is_executing = True
        self.current_task = task
        
        try:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.utcnow()
            
            logger.info(
                "Task execution started",
                task_id=task.id,
                title=task.title,
                steps_count=len(task.steps),
                adaptive=adaptive,
                session_id=self.session_id
            )
            
            yield {
                "type": "task_started",
                "data": {
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "steps_count": len(task.steps),
                    "adaptive": adaptive
                }
            }
            
            # Execute each step
            for i, step in enumerate(task.steps):
                logger.info(
                    "Executing task step",
                    task_id=task.id,
                    step_id=step.id,
                    step_number=i + 1,
                    total_steps=len(task.steps)
                )
                
                yield {
                    "type": "step_started",
                    "data": {
                        "task_id": task.id,
                        "step_id": step.id,
                        "step_number": i + 1,
                        "total_steps": len(task.steps),
                        "description": step.description
                    }
                }
                
                # Execute step
                completed_step = await self.task_executor.execute_step(
                    step,
                    self.session_id
                )
                
                yield {
                    "type": "step_completed",
                    "data": {
                        "task_id": task.id,
                        "step_id": completed_step.id,
                        "status": completed_step.status.value,
                        "result": completed_step.result,
                        "error": completed_step.error,
                        "execution_time": completed_step.execution_time
                    }
                }
                
                # Check if step failed
                if completed_step.status == TaskStatus.FAILED:
                    if adaptive:
                        # Try to adapt and continue
                        logger.warning(
                            "Task step failed, attempting adaptation",
                            task_id=task.id,
                            step_id=step.id,
                            error=step.error
                        )
                        
                        # Create recovery step
                        recovery_step = await self._create_recovery_step(
                            task, completed_step, i + 1
                        )
                        
                        if recovery_step:
                            task.steps.insert(i + 1, recovery_step)
                            
                            yield {
                                "type": "step_adapted",
                                "data": {
                                    "task_id": task.id,
                                    "failed_step_id": step.id,
                                    "recovery_step_id": recovery_step.id,
                                    "recovery_description": recovery_step.description
                                }
                            }
                    else:
                        # Stop execution on failure
                        task.status = TaskStatus.FAILED
                        break
            
            # Determine final task status
            if all(step.status == TaskStatus.COMPLETED for step in task.steps):
                task.status = TaskStatus.COMPLETED
            elif any(step.status == TaskStatus.FAILED for step in task.steps):
                task.status = TaskStatus.FAILED
            else:
                task.status = TaskStatus.COMPLETED  # Partial completion
            
            task.completed_at = datetime.utcnow()
            
            logger.info(
                "Task execution completed",
                task_id=task.id,
                status=task.status.value,
                duration_seconds=(task.completed_at - task.started_at).total_seconds() if task.started_at else 0,
                session_id=self.session_id
            )
            
            yield {
                "type": "task_completed",
                "data": {
                    "task_id": task.id,
                    "status": task.status.value,
                    "steps_completed": len([s for s in task.steps if s.status == TaskStatus.COMPLETED]),
                    "steps_failed": len([s for s in task.steps if s.status == TaskStatus.FAILED]),
                    "total_steps": len(task.steps),
                    "duration_seconds": (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
                }
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow()
            
            logger.error(
                "Task execution failed",
                task_id=task.id,
                session_id=self.session_id,
                error=str(e),
                exc_info=True
            )
            
            yield {
                "type": "task_failed",
                "data": {
                    "task_id": task.id,
                    "error": str(e)
                }
            }
            
        finally:
            self.is_executing = False
    
    async def _create_recovery_step(
        self,
        task: Task,
        failed_step: TaskStep,
        step_number: int
    ) -> Optional[TaskStep]:
        """Create a recovery step for a failed step."""
        
        try:
            # Simple recovery strategy - retry with different approach
            recovery_description = f"Recovery for failed step: {failed_step.description}"
            
            # Create a recovery step that might use different tools or approach
            recovery_step = TaskStep(
                id=f"recovery_{step_number}",
                description=recovery_description,
                tool_calls=[]  # Start with no tools, let LLM decide
            )
            
            logger.info(
                "Recovery step created",
                task_id=task.id,
                failed_step_id=failed_step.id,
                recovery_step_id=recovery_step.id,
                session_id=self.session_id
            )
            
            return recovery_step
            
        except Exception as e:
            logger.error(
                "Failed to create recovery step",
                task_id=task.id,
                failed_step_id=failed_step.id,
                error=str(e),
                session_id=self.session_id
            )
            return None
    
    def get_current_task(self) -> Optional[Task]:
        """Get the currently executing task."""
        return self.current_task
    
    def is_task_executing(self) -> bool:
        """Check if a task is currently executing."""
        return self.is_executing