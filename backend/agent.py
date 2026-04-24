"""Core agent orchestrator for the autonomous agent system."""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
import structlog
import re

from config import settings
from memory import MemoryManager, ToolCall
from tools import get_tool_registry, ParallelToolExecutor
from services.llm_service import get_llm_service, LLMService
from services.session_manager import Session
from errors.exceptions import AgentError, ToolExecutionError, LLMServiceError
from errors.recovery import RetryStrategy, GracefulDegradation
from agent_logging.metrics import metrics, performance_timer
from services.rag_service import retrieve

logger = structlog.get_logger()


class AutonomousAgent:
    """Core agent orchestrator that coordinates LLM, tools, and memory."""
    
    def __init__(
        self,
        session: Session,
        llm_service: Optional[LLMService] = None,
        tool_executor: Optional[ParallelToolExecutor] = None,
        preview_service = None
    ):
        self.session = session
        self.memory = session.memory
        
        # Initialize services
        self.llm_service = llm_service or get_llm_service()
        self.tool_registry = get_tool_registry()
        self.tool_executor = tool_executor or ParallelToolExecutor(self.tool_registry)
        self.preview_service = preview_service
        
        # Recovery strategies
        self.retry_strategy = RetryStrategy(
            max_attempts=settings.retry_attempts,
            initial_delay=settings.retry_delay
        )
        
        # Agent state
        self.is_processing = False
        self.current_task = None
        
        # Flutter system prompt will be initialized on first chat call
    
    async def _ensure_system_prompt(self):
        """Ensure Flutter development system prompt is set."""
        # Check if system prompt already exists
        if not self.memory.messages or self.memory.messages[0].role != "system":
            # Add Flutter development system prompt
            flutter_prompt = """You are a Flutter development AI assistant specialized in creating complete, functional Flutter applications for the Fluxo platform.

CORE RESPONSIBILITIES:
1. Generate complete Flutter applications based on user requirements
2. Create well-structured Dart code with proper architecture
3. Generate projects that can be built and run immediately
4. Always use the Fluxo design system — dark theme, brand colors, consistent identity

FLUTTER CODE REQUIREMENTS:
- CRITICAL: Put ALL code in a single lib/main.dart file. Do NOT create separate files like models/, widgets/, repository/, etc.
- Define all classes (models, widgets, state) directly inside lib/main.dart
- Always generate a complete, self-contained lib/main.dart
- CRITICAL: Do NOT use any external packages (e.g. shared_preferences, provider, http, dio, get, riverpod, bloc, sqflite, hive, firebase_*, etc.)
- ONLY use packages already included in a default Flutter project: flutter/material.dart, flutter/widgets.dart, dart:math, dart:convert, dart:async, dart:collection
- All state must be managed with built-in StatefulWidget — no external state management
- All data must be stored in-memory (List, Map) — no persistence packages
- Include all necessary imports at the top of main.dart
- Write production-ready code with error handling
- Use StatefulWidget for interactive features
- Follow Flutter naming conventions

FLUXO DESIGN SYSTEM — MANDATORY FOR EVERY APP:
Every app you build MUST use this exact design system. No exceptions.

Brand Colors:
- Accent / Primary: #44D62C  (Fluxo green)
- Background:       #141414
- Surface:          #1A1A1A
- Surface raised:   #222222
- Border:           #363636
- Text primary:     #F0F0F0
- Text secondary:   #B0B0B0
- Text muted:       #787878

ALWAYS use this ThemeData in MaterialApp — copy it exactly:
```dart
theme: ThemeData(
  brightness: Brightness.dark,
  scaffoldBackgroundColor: const Color(0xFF141414),
  primaryColor: const Color(0xFF44D62C),
  colorScheme: const ColorScheme.dark(
    primary: Color(0xFF44D62C),
    secondary: Color(0xFF44D62C),
    surface: Color(0xFF1A1A1A),
    onPrimary: Colors.black,
    onSecondary: Colors.black,
    onSurface: Color(0xFFF0F0F0),
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: Color(0xFF1A1A1A),
    foregroundColor: Color(0xFFF0F0F0),
    elevation: 0,
    centerTitle: false,
    titleTextStyle: TextStyle(
      color: Color(0xFFF0F0F0),
      fontSize: 18,
      fontWeight: FontWeight.w600,
      letterSpacing: -0.3,
    ),
  ),
  cardColor: const Color(0xFF1A1A1A),
  dividerColor: const Color(0xFF363636),
  floatingActionButtonTheme: const FloatingActionButtonThemeData(
    backgroundColor: Color(0xFF44D62C),
    foregroundColor: Colors.black,
  ),
  elevatedButtonTheme: ElevatedButtonThemeData(
    style: ElevatedButton.styleFrom(
      backgroundColor: const Color(0xFF44D62C),
      foregroundColor: Colors.black,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: const Color(0xFF222222),
    border: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: Color(0xFF363636)),
    ),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: Color(0xFF363636)),
    ),
    focusedBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: Color(0xFF44D62C)),
    ),
    labelStyle: const TextStyle(color: Color(0xFF787878)),
    hintStyle: const TextStyle(color: Color(0xFF787878)),
  ),
  textTheme: const TextTheme(
    bodyLarge: TextStyle(color: Color(0xFFF0F0F0)),
    bodyMedium: TextStyle(color: Color(0xFFB0B0B0)),
    bodySmall: TextStyle(color: Color(0xFF787878)),
    titleLarge: TextStyle(color: Color(0xFFF0F0F0), fontWeight: FontWeight.w600),
    titleMedium: TextStyle(color: Color(0xFFF0F0F0), fontWeight: FontWeight.w500),
  ),
),
```

BRANDING RULES:
- Set MaterialApp title to 'Fluxo' always
- Set debugShowCheckedModeBanner: false always
- AppBar leading icon: use a green lightning bolt ⚡ (Icon(Icons.bolt, color: Color(0xFF44D62C)))
- NEVER use light theme, NEVER use Colors.blue, NEVER use default primarySwatch
- All Scaffold backgrounds must be Color(0xFF141414)
- Cards and containers use Color(0xFF1A1A1A) with border Color(0xFF363636)
- Interactive accent elements (buttons, highlights, selections) use Color(0xFF44D62C)
- Text on green backgrounds must always be Colors.black

RESPONSE FORMAT:
When creating Flutter applications, provide:
1. Brief description of what you're building
2. Complete lib/main.dart code (single file, all classes inside, no external packages)

EXAMPLE STRUCTURE:
```dart
import 'package:flutter/material.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fluxo',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF141414),
        primaryColor: const Color(0xFF44D62C),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF44D62C),
          secondary: Color(0xFF44D62C),
          surface: Color(0xFF1A1A1A),
          onPrimary: Colors.black,
          onSecondary: Colors.black,
          onSurface: Color(0xFFF0F0F0),
        ),
        // ... (full theme as above)
      ),
      home: const HomePage(),
    );
  }
}
```

Always focus on creating functional, visually appealing Flutter applications that feel native to the Fluxo platform."""

            await self.memory.add_message("system", flutter_prompt)
        
    async def _complexity_check(self, user_message: str) -> Dict[str, Any]:
        """One cheap LLM call to decide if a request needs a planning conversation."""
        prompt = f"""You are evaluating a Flutter app request to decide if upfront planning is needed.

Request: "{user_message}"

Classify as "simple" if the app is clearly a single-screen utility with no ambiguity (counter, timer, basic todo, calculator, color picker, stopwatch, etc.).
Classify as "complex" if the app has multiple screens, charts, data relationships, real-time features, auth, or any ambiguity that benefits from clarification.

Respond with valid JSON only — no markdown, no explanation:
{{
  "complexity": "simple",
  "plan_summary": "one sentence describing what you will build",
  "questions": []
}}

Or for complex:
{{
  "complexity": "complex",
  "plan_summary": "one sentence describing what you will build",
  "questions": ["specific question 1", "specific question 2"]
}}

Maximum 3 questions. Questions must be specific and directly affect how you build the app."""

        try:
            response = await self.llm_service.complete_chat(
                messages=[{"role": "user", "content": prompt}],
                tools=[]
            )
            content = response.get("content", "")
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                if "complexity" in result:
                    return result
        except Exception as e:
            logger.warning("Complexity check failed, defaulting to simple", error=str(e))

        return {"complexity": "simple", "plan_summary": "", "questions": []}

    async def _planning_pass(self, user_message: str, is_new_project: bool) -> str:
        
        prompt = " "
        available_tools = self.tool_executor.get_available_tools()
        
        if is_new_project:
            prompt = f"""You are a Flutter planning assistant. 
                User wants to build: "{user_message}". 
                List the specific Flutter widgets, state patterns, and layout concepts needed to build this. 
                Return a concise comma-separated list of Flutter terms only. No code, no explanation. 
                """
        else:
            prompt = f""" You are a Flutter planning assistant.
                The user wants to make this change: "{user_message}"
                Use the read_file tool to read lib/main.dart and understand what already exists.
                Then list the specific Flutter widgets and patterns involved in this change.
                Return a concise comma-separated list of Flutter terms only. No code, no explanation.
                """
                
        if is_new_project: 
            tools = []
        else:
            tools = [tool["schema"] for tool in available_tools]
            
        response = await self.llm_service.complete_chat(
            messages=[{"role": "user", "content": prompt}],
            tools=tools
        )
        
        return response.get("content") or user_message

    async def chat(
        self,
        user_message: str,
        stream: bool = False,
        autonomous: bool = True,
        max_iterations: int = 10
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Main chat interface with Cursor-like efficiency.
        
        Implements single chat completion with parallel tool execution
        and context preservation like Cursor's approach.
        """
        
        if self.is_processing:
            yield {
                "type": "error",
                "data": {"error": "Agent is already processing a request"}
            }
            return
        
        self.is_processing = True

        try:
            # Ensure Flutter system prompt is set
            await self._ensure_system_prompt()

            # is_new_project = no Flutter code built yet (idle or mid-planning)
            is_new_project = self.session.phase in ("idle", "planning")

            # ── Planning Gate ────────────────────────────────────────────────────
            if self.session.phase == "idle":
                yield {"type": "status", "data": {"message": "Analyzing your request..."}}
                check = await self._complexity_check(user_message)

                if check["complexity"] == "complex" and check.get("questions"):
                    # Complex request — enter planning phase
                    self.session.phase = "planning"
                    await self.memory.add_message("user", user_message)
                    self.session.increment_message_count()

                    # Store plan as an assistant turn so the LLM has full context later
                    plan_text = (
                        f"Plan: {check['plan_summary']}\n\n"
                        + "\n".join(f"{i+1}. {q}" for i, q in enumerate(check["questions"]))
                    )
                    await self.memory.add_message("assistant", plan_text)

                    yield {
                        "type": "plan",
                        "data": {
                            "summary": check["plan_summary"],
                            "questions": check["questions"],
                        },
                    }
                    return  # wait for user's answers

                # Simple request — skip planning, go straight to building
                self.session.phase = "building"

            elif self.session.phase == "planning":
                # User just answered the planning questions
                self.session.phase = "building"
                yield {"type": "status", "data": {"message": "Got it! Starting to build..."}}

            # ── Add user message and proceed to build ───────────────────────────
            await self.memory.add_message("user", user_message)
            self.session.increment_message_count()

            yield {
                "type": "status",
                "data": {"message": "Processing request...", "autonomous": autonomous},
            }

            # Proactively prepare Flutter container before AI processing
            # Block until container is confirmed ready before calling OpenAI
            container_info = await self._wait_for_container_ready()
            if container_info:
                yield {
                    "type": "flutter_preview",
                    "data": container_info
                }
            else:
                yield {
                    "type": "status",
                    "data": {"message": "Flutter container failed to start, cannot proceed"}
                }
                return
            
            # Planning pass to determine what to build
            loop = asyncio.get_event_loop()
            rag_query = await self._planning_pass(user_message, is_new_project)
            rag_chunks = await loop.run_in_executor(None, retrieve, rag_query)
            
            # Get conversation history
            messages = await self.memory.get_conversation_history()
            
            # Inject RAG context
            if rag_chunks:
                rag_context = "\n\n-------\n\n".join(rag_chunks)
                messages.append({
                    "role": "system",
                    "content": f"### Relevant Documentation\n\n{rag_context}"
                })
            
            # Main processing loop with autonomous iterations
            iteration = 0
            
            while iteration < max_iterations:
                iteration += 1
                
                logger.info(
                    "Agent iteration started",
                    session_id=self.session.session_id,
                    iteration=iteration,
                    autonomous=autonomous
                )
                
                # Get available tools
                available_tools = self.tool_executor.get_available_tools()
                tools_schema = [tool["schema"] for tool in available_tools]
                
                try:
                    # Single chat completion with tools (Cursor approach)
                    async with performance_timer(
                        "agent_llm_completion",
                        {"session_id": self.session.session_id, "iteration": iteration}
                    ):
                        if stream and iteration == 1:
                            # Stream first response
                            async for chunk in self._process_llm_stream(messages, tools_schema):
                                yield chunk
                        else:
                            # Non-streaming for tool iterations
                            response = await self.llm_service.complete_chat(
                                messages=messages,
                                tools=tools_schema
                            )
                            
                            # Process LLM response
                            async for result in self._process_llm_response(response, iteration):
                                yield result
                    
                    # Check if we need to continue (tool calls were made)
                    if not autonomous:
                        break
                    
                    # Re-fetch messages to get the latest assistant response
                    fresh_messages = await self.memory.get_conversation_history()
                    last_message = fresh_messages[-1] if fresh_messages else None
                    if (last_message and
                        last_message.get("role") == "assistant" and
                        not last_message.get("tool_calls")):
                        break
                    
                except LLMServiceError as e:
                    logger.error(
                        "LLM service error in agent iteration",
                        session_id=self.session.session_id,
                        iteration=iteration,
                        error=str(e)
                    )
                    
                    # Try graceful degradation
                    fallback_response = await GracefulDegradation.fallback_to_simple_response(
                        e, {"session_id": self.session.session_id}
                    )
                    
                    yield {
                        "type": "content",
                        "data": fallback_response
                    }
                    
                    break
                
                except Exception as e:
                    logger.error(
                        "Unexpected error in agent iteration",
                        session_id=self.session.session_id,
                        iteration=iteration,
                        error=str(e),
                        exc_info=True
                    )
                    
                    yield {
                        "type": "error",
                        "data": {"error": f"Unexpected error: {str(e)}"}
                    }
                    
                    break
            
            yield {
                "type": "done",
                "data": {
                    "iterations": iteration,
                    "session_id": self.session.session_id,
                    "autonomous": autonomous
                }
            }
            
        finally:
            self.is_processing = False
    
    async def _process_llm_stream(
        self, 
        messages: List[Dict[str, Any]], 
        tools: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process streaming LLM response."""
        
        accumulated_content = ""
        tool_calls = []
        
        async for chunk in self.llm_service.complete_chat_stream(
            messages=messages,
            tools=tools
        ):
            if chunk["type"] == "content":
                accumulated_content += chunk["data"]
                yield chunk
                
            elif chunk["type"] == "tool_call":
                tool_calls.append(chunk["data"])
                yield chunk
                
            elif chunk["type"] == "done":
                # Add assistant message to memory
                await self.memory.add_message(
                    "assistant",
                    accumulated_content,
                    tool_calls=tool_calls if tool_calls else None
                )

                # Process tool calls if any
                if tool_calls:
                    async for tool_result in self._execute_tools_parallel(tool_calls):
                        yield tool_result

                # Check for Flutter code and write to container
                if accumulated_content and self._contains_flutter_code(accumulated_content):
                    async for update_chunk in self._update_flutter_container_stepwise(accumulated_content):
                        yield update_chunk

                yield chunk
    
    async def _process_llm_response(
        self, 
        response: Dict[str, Any],
        iteration: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Process non-streaming LLM response."""
        
        content = response.get("content", "")
        tool_calls = response.get("tool_calls")
        
        # Yield content if present
        if content:
            yield {
                "type": "content",
                "data": content
            }
        
        # Check for Flutter code and update existing container step-by-step
        if content and self._contains_flutter_code(content):
            try:
                yield {
                    "type": "status",
                    "data": {"message": "🔄 Updating Flutter application with AI-generated code..."}
                }
                
                # Update container with step-by-step file writing
                async for update_chunk in self._update_flutter_container_stepwise(content):
                    yield update_chunk
                    
            except Exception as e:
                logger.warning(f"Failed to update Flutter container: {e}")
                yield {
                    "type": "status",
                    "data": {"message": f"❌ Failed to update Flutter container: {e}"}
                }
        
        # Add assistant message to memory
        await self.memory.add_message(
            "assistant",
            content,
            tool_calls=tool_calls
        )
        
        # Execute tools if present
        if tool_calls:
            async for tool_result in self._execute_tools_parallel(tool_calls):
                yield tool_result
    
    async def _execute_tools_parallel(
        self, 
        tool_calls: List[Dict[str, Any]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Execute tools in parallel like Cursor's approach.
        
        This is the key efficiency improvement - executing multiple tools
        simultaneously instead of sequentially.
        """
        
        logger.info(
            "Executing tools in parallel",
            session_id=self.session.session_id,
            tool_count=len(tool_calls)
        )
        
        yield {
            "type": "tools_start",
            "data": {
                "tool_count": len(tool_calls),
                "parallel": True
            }
        }
        
        # Convert tool calls to executor format
        executor_tool_calls = []
        for tool_call in tool_calls:
            if isinstance(tool_call.get("function", {}).get("arguments"), str):
                # Parse JSON arguments
                try:
                    arguments = json.loads(tool_call["function"]["arguments"])
                except json.JSONDecodeError as e:
                    logger.error(
                        "Invalid JSON in tool arguments",
                        tool_call=tool_call,
                        error=str(e)
                    )
                    arguments = {}
            else:
                arguments = tool_call.get("function", {}).get("arguments", {})
            
            executor_tool_calls.append({
                "id": tool_call.get("id"),
                "name": tool_call.get("function", {}).get("name"),
                "arguments": arguments
            })
        
        # Execute tools in parallel
        successful_results, errors = await self.tool_executor.execute_tools_parallel(
            executor_tool_calls,
            session_id=self.session.session_id
        )
        
        # Process results
        tool_messages = []
        
        for call_id, result in successful_results.items():
            yield {
                "type": "tool_result",
                "data": {
                    "call_id": call_id,
                    "success": True,
                    "result": result.data,
                    "execution_time": result.execution_time
                }
            }
            
            # Cache successful tool result
            matching_tool_call = next(
                (tc for tc in executor_tool_calls if tc.get("id") == call_id), 
                None
            )
            
            if matching_tool_call:
                tool_call_obj = ToolCall(
                    tool_name=matching_tool_call["name"],
                    arguments=matching_tool_call["arguments"],
                    result=result.data,
                    execution_time=result.execution_time
                )
                await self.memory.cache_tool_call(tool_call_obj)
            
            # Prepare tool message for LLM
            tool_messages.append({
                "role": "tool", 
                "tool_call_id": call_id,
                "content": json.dumps(result.data) if result.data else ""
            })
        
        # Handle errors
        for call_id, error in errors.items():
            yield {
                "type": "tool_error",
                "data": {
                    "call_id": call_id,
                    "error": error
                }
            }
            
            # Add error message for LLM
            tool_messages.append({
                "role": "tool",
                "tool_call_id": call_id,
                "content": f"Error: {error}"
            })
            
            self.session.increment_error_count()
        
        # Add tool results to memory
        if tool_messages:
            for tool_msg in tool_messages:
                await self.memory.add_message(
                    tool_msg["role"],
                    tool_msg["content"],
                    metadata={
                        "tool_call_id": tool_msg.get("tool_call_id")
                    }
                )
        
        self.session.increment_tool_calls()
        
        yield {
            "type": "tools_complete",
            "data": {
                "successful": len(successful_results),
                "failed": len(errors),
                "total": len(tool_calls)
            }
        }
    
    async def get_context_summary(self) -> Dict[str, Any]:
        """Get current conversation context summary."""
        
        try:
            conversation_history = await self.memory.get_conversation_history()
            
            return {
                "session_id": self.session.session_id,
                "message_count": len(conversation_history),
                "last_activity": self.session.last_activity.isoformat(),
                "tool_calls_count": self.session.tool_calls_count,
                "error_count": self.session.error_count,
                "is_processing": self.is_processing,
                "available_tools": len(self.tool_registry.list_tools()),
                "llm_service": self.llm_service.service_name
            }
            
        except Exception as e:
            logger.error(
                "Failed to get context summary",
                session_id=self.session.session_id,
                error=str(e),
                exc_info=True
            )
            raise AgentError(f"Failed to get context summary: {e}")
    
    async def clear_context(self, keep_system_messages: bool = True) -> bool:
        """Clear conversation context."""
        
        try:
            if keep_system_messages:
                # Keep only system messages
                history = await self.memory.get_conversation_history(include_system=True)
                system_messages = [msg for msg in history if msg.get("role") == "system"]
                
                # Reset memory
                self.memory.messages.clear()
                
                # Re-add system messages
                for msg in system_messages:
                    await self.memory.add_message(
                        msg["role"],
                        msg["content"],
                        metadata=msg.get("metadata")
                    )
            else:
                # Clear everything
                self.memory.messages.clear()
            
            # Clear tool cache
            self.memory.tool_calls_cache.clear()
            
            logger.info(
                "Context cleared",
                session_id=self.session.session_id,
                keep_system_messages=keep_system_messages
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to clear context",
                session_id=self.session.session_id,
                error=str(e),
                exc_info=True
            )
            return False
    
    async def _wait_for_container_ready(self) -> Optional[Dict[str, Any]]:
        """Block until Flutter container confirms ready, then return container info."""
        if not (hasattr(self, 'preview_service') and self.preview_service):
            return None

        async for event in self.preview_service.warmup_session(self.session.session_id):
            logger.info("Container warmup phase", phase=event["phase"], message=event["message"])
            if event["phase"] == "container_ready":
                return {
                    "success": True,
                    "previewUrl": event.get("previewUrl"),
                    "message": "Flutter container ready"
                }
            elif event["phase"] == "error":
                logger.error("Container warmup failed", message=event["message"])
                return None

        return None

    async def _prepare_flutter_container(self) -> Optional[Dict[str, Any]]:
        """Proactively prepare Flutter container before AI processing."""
        try:
            # Import preview service here to avoid circular imports
            from services.flutter_preview_service import FlutterPreviewService
            
            # Use the preview service instance from the agent
            if hasattr(self, 'preview_service') and self.preview_service:
                preview_service = self.preview_service
            else:
                # Fallback to creating new instance (not ideal but works)
                preview_service = FlutterPreviewService()
            
            # Create a basic Flutter app template to initialize the container
            basic_flutter_files = [
                {
                    "filename": "lib/main.dart",
                    "content": """import 'package:flutter/material.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Flutter Development Environment',
      theme: ThemeData(
        primarySwatch: Colors.blue,
      ),
      home: Scaffold(
        appBar: AppBar(
          title: Text('Flutter Development Environment'),
        ),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.flutter_dash,
                size: 64,
                color: Colors.blue,
              ),
              SizedBox(height: 16),
              Text(
                'Flutter Development Environment Ready',
                style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
              ),
              SizedBox(height: 8),
              Text(
                'Waiting for AI to generate your application...',
                style: TextStyle(color: Colors.grey[600]),
              ),
            ],
          ),
        ),
      ),
    );
  }
}"""
                }
            ]
            
            # Use session-based container management to get or create container
            result = await preview_service.get_or_create_session(
                main_session_id=self.session.session_id, 
                files=basic_flutter_files
            )
            
            if result.get("success"):
                logger.info(
                    "Flutter container prepared proactively",
                    session_id=self.session.session_id,
                    preview_session_id=result.get("sessionId"),
                    preview_url=result.get("previewUrl", ""),
                    port=result.get("port")
                )
                return {
                    "success": True,
                    "sessionId": result.get("sessionId"),
                    "previewUrl": result.get("previewUrl"),
                    "port": result.get("port"),
                    "message": "Flutter development environment ready"
                }
            else:
                logger.warning(
                    "Failed to prepare Flutter container proactively",
                    session_id=self.session.session_id,
                    error=result.get("error", "Unknown error")
                )
                return None
                        
        except Exception as e:
            logger.error(
                f"Error preparing Flutter container: {e}",
                session_id=self.session.session_id,
                exc_info=True
            )
            return None

    async def _update_flutter_container_stepwise(self, content: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Copy AI-generated code into build container, build, and serve static output."""
        try:
            dart_code = self._extract_dart_code(content)
            if not dart_code:
                yield {"type": "status", "data": {"message": "⚠️ No valid Dart code found in AI response"}}
                return

            if not (hasattr(self, 'preview_service') and self.preview_service):
                yield {"type": "status", "data": {"message": "❌ Build service not available"}}
                return

            yield {"type": "status", "data": {"message": "💾 Copying files into build container..."}}

            files = [{"filename": "lib/main.dart", "content": dart_code}]

            # Emit files so the frontend can populate the file explorer
            yield {"type": "files", "data": [{"path": f["filename"], "content": f["content"]} for f in files]}

            yield {"type": "status", "data": {"message": "🔨 Building Flutter web app..."}}

            result = await self.preview_service.build_project(self.session.session_id, files)

            if result.get("success"):
                logger.info(
                    "Flutter container updated with AI-generated code",
                    session_id=self.session.session_id,
                    preview_url=result.get("previewUrl")
                )
                yield {
                    "type": "flutter_preview_update",
                    "data": {
                        "success": True,
                        "previewUrl": result.get("previewUrl"),
                        "message": "Flutter application built successfully"
                    }
                }
                yield {"type": "status", "data": {"message": "🎉 Flutter application built and ready!"}}
            else:
                logger.error("Build failed", session_id=self.session.session_id, error=result.get("error"))
                build_output = result.get("output", "")
                # Extract the first meaningful error lines from compiler output
                error_lines = [l for l in build_output.splitlines() if "Error:" in l or "error:" in l]
                error_summary = "\n".join(error_lines[:8]) if error_lines else result.get("error", "Unknown error")
                yield {"type": "build_error", "data": {"message": f"Build failed", "detail": error_summary}}

        except Exception as e:
            logger.error(
                "Error updating Flutter container",
                session_id=self.session.session_id,
                error=str(e),
                exc_info=True
            )
            yield {"type": "status", "data": {"message": f"❌ Error during build: {str(e)}"}}

    async def _update_flutter_container(self, content: str) -> Optional[Dict[str, Any]]:
        """Update existing Flutter container with AI-generated code."""
        try:
            # Extract Dart code from content
            dart_code = self._extract_dart_code(content)
            if not dart_code:
                logger.warning("No valid Dart code found in AI response")
                return None
            
            # Import preview service here to avoid circular imports
            from services.flutter_preview_service import FlutterPreviewService
            
            # Use the preview service instance from the agent
            if hasattr(self, 'preview_service') and self.preview_service:
                preview_service = self.preview_service
            else:
                # Fallback to creating new instance (not ideal but works)
                preview_service = FlutterPreviewService()
            
            # Format code as files array
            files = [
                {
                    "filename": "lib/main.dart",
                    "content": dart_code
                }
            ]
            
            # Update the existing container (this will trigger hot reload)
            result = await preview_service.get_or_create_session(
                main_session_id=self.session.session_id, 
                files=files
            )
            
            if result.get("success"):
                logger.info(
                    "Flutter container updated with AI-generated code",
                    session_id=self.session.session_id,
                    preview_session_id=result.get("sessionId"),
                    preview_url=result.get("previewUrl", ""),
                    port=result.get("port")
                )
                return {
                    "success": True,
                    "sessionId": result.get("sessionId"),
                    "previewUrl": result.get("previewUrl"),
                    "port": result.get("port"),
                    "message": "Flutter application updated with AI-generated code"
                }
            else:
                logger.warning(
                    "Failed to update Flutter container",
                    session_id=self.session.session_id,
                    error=result.get("error", "Unknown error")
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": "Failed to update Flutter application"
                }
                        
        except Exception as e:
            logger.error(
                f"Error updating Flutter container: {e}",
                session_id=self.session.session_id,
                exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to update Flutter application"
            }

    def _contains_flutter_code(self, content: str) -> bool:
        """Check if content contains Flutter/Dart code."""
        flutter_indicators = [
            "import 'package:flutter/material.dart'",
            "runApp(",
            "StatelessWidget",
            "StatefulWidget",
            "MaterialApp",
            "Scaffold",
            "@override",
            "Widget build(",
            "```dart"
        ]
        
        content_lower = content.lower()
        return any(indicator.lower() in content_lower for indicator in flutter_indicators)
    
    async def _send_to_preview_server(self, content: str):
        """Send Flutter code to integrated preview service for live preview."""
        try:
            # Extract Dart code from content
            dart_code = self._extract_dart_code(content)
            if not dart_code:
                return None
            
            # Import preview service here to avoid circular imports
            from services.flutter_preview_service import FlutterPreviewService
            
            # Format code as files array
            files = [
                {
                    "filename": "lib/main.dart",
                    "content": dart_code
                }
            ]
            
            # Use the preview service instance from the agent
            if hasattr(self, 'preview_service') and self.preview_service:
                preview_service = self.preview_service
            else:
                # Fallback to creating new instance (not ideal but works)
                preview_service = FlutterPreviewService()
            
            # Use session-based container management
            result = await preview_service.get_or_create_session(
                main_session_id=self.session.session_id, 
                files=files
            )
            
            if result.get("success"):
                logger.info(
                    "Flutter code sent to preview service",
                    session_id=self.session.session_id,
                    preview_session_id=result.get("sessionId"),
                    preview_url=result.get("previewUrl", ""),
                    port=result.get("port")
                )
                return {
                    "success": True,
                    "sessionId": result.get("sessionId"),
                    "previewUrl": result.get("previewUrl"),
                    "port": result.get("port"),
                    "message": "Flutter preview created successfully"
                }
            else:
                logger.warning(
                    "Preview service failed to create session",
                    session_id=self.session.session_id,
                    error=result.get("error", "Unknown error")
                )
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error"),
                    "message": "Failed to create Flutter preview"
                }
                        
        except Exception as e:
            logger.error(
                f"Error sending to preview service: {e}",
                session_id=self.session.session_id,
                exc_info=True
            )
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create Flutter preview"
            }
    
    def _extract_dart_code(self, content: str) -> str:
        """Extract Dart code from markdown or plain text."""
        # Look for code blocks first
        dart_code_pattern = r'```dart\s*(.*?)```'
        matches = re.findall(dart_code_pattern, content, re.DOTALL | re.IGNORECASE)
        
        if matches:
            return matches[0].strip()
        
        # If no code blocks, look for Flutter imports as start
        if "import 'package:flutter/material.dart'" in content:
            # Find the start of Dart code
            lines = content.split('\n')
            dart_lines = []
            in_dart_code = False
            
            for line in lines:
                if "import 'package:flutter/material.dart'" in line:
                    in_dart_code = True
                
                if in_dart_code:
                    dart_lines.append(line)
            
            return '\n'.join(dart_lines).strip()
        
        return ""