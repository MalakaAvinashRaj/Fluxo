"""LLM service integrations for OpenAI and Anthropic."""

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Union
import openai
import anthropic
import structlog

from config import settings
from errors.exceptions import LLMServiceError
from errors.recovery import CircuitBreaker
from agent_logging.metrics import metrics, performance_timer
from memory import Message

logger = structlog.get_logger()


class LLMService(ABC):
    """Abstract base class for LLM services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=settings.circuit_breaker_threshold,
            recovery_timeout=60.0,
            expected_exception=LLMServiceError
        )
    
    @abstractmethod
    async def complete_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete chat conversation."""
        pass
    
    @abstractmethod
    async def complete_chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Complete chat conversation with streaming."""
        pass
    
    async def _execute_with_circuit_breaker(self, operation, *args, **kwargs):
        """Execute operation through circuit breaker."""
        
        try:
            return await self.circuit_breaker.call(operation, *args, **kwargs)
        except Exception as e:
            logger.error(
                "LLM service operation failed",
                service=self.service_name,
                error=str(e),
                exc_info=True
            )
            raise LLMServiceError(
                f"LLM service '{self.service_name}' failed: {str(e)}",
                service=self.service_name
            )


class OpenAIService(LLMService):
    """OpenAI GPT service implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("openai")
        
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise LLMServiceError("OpenAI API key not provided", service="openai")
        
        self.client = openai.AsyncOpenAI(api_key=self.api_key)
        self.default_model = settings.default_model
    
    async def complete_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete chat using OpenAI GPT."""
        
        async def _complete():
            model_name = model or self.default_model
            
            # Prepare request parameters
            # gpt-5 and o-series models use max_completion_tokens; everything else uses max_tokens
            uses_new_params = model_name.startswith(("gpt-5", "o1", "o3", "o4"))
            params = {
                "model": model_name,
                "messages": messages,
                "max_completion_tokens" if uses_new_params else "max_tokens":
                    kwargs.get("max_tokens", settings.max_tokens),
            }

            # o-series and gpt-5 don't support temperature
            if not uses_new_params:
                params["temperature"] = kwargs.get("temperature", settings.temperature)
            
            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = kwargs.get("tool_choice", "auto")
            
            logger.info(
                "Making OpenAI API request",
                model=model_name,
                message_count=len(messages),
                has_tools=bool(tools)
            )
            
            async with performance_timer("openai_chat_completion"):
                try:
                    response = await self.client.chat.completions.create(**params)
                    
                    # Extract response data
                    result = {
                        "content": response.choices[0].message.content,
                        "role": "assistant",
                        "tool_calls": None,
                        "usage": {
                            "prompt_tokens": response.usage.prompt_tokens,
                            "completion_tokens": response.usage.completion_tokens,
                            "total_tokens": response.usage.total_tokens
                        },
                        "model": response.model,
                        "finish_reason": response.choices[0].finish_reason
                    }
                    
                    # Handle tool calls if present
                    if response.choices[0].message.tool_calls:
                        tool_calls = []
                        for tool_call in response.choices[0].message.tool_calls:
                            tool_calls.append({
                                "id": tool_call.id,
                                "type": tool_call.type,
                                "function": {
                                    "name": tool_call.function.name,
                                    "arguments": tool_call.function.arguments
                                }
                            })
                        result["tool_calls"] = tool_calls
                    
                    # Record metrics
                    metrics.record_llm_request(
                        service="openai",
                        model=model_name,
                        status="success",
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens
                    )
                    
                    logger.info(
                        "OpenAI API request completed",
                        model=model_name,
                        finish_reason=result["finish_reason"],
                        total_tokens=response.usage.total_tokens,
                        has_tool_calls=bool(result["tool_calls"])
                    )
                    
                    return result
                    
                except openai.APIError as e:
                    logger.error(
                        "OpenAI API error",
                        error=str(e),
                        status_code=getattr(e, 'status_code', None),
                        exc_info=True
                    )
                    
                    # Record error metrics
                    metrics.record_llm_request(
                        service="openai",
                        model=model_name,
                        status="error",
                        prompt_tokens=0,
                        completion_tokens=0
                    )
                    
                    raise LLMServiceError(
                        f"OpenAI API error: {str(e)}",
                        service="openai"
                    )
        
        return await self._execute_with_circuit_breaker(_complete)
    
    async def complete_chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from OpenAI."""
        
        model_name = model or self.default_model
        
        # Prepare request parameters
        # gpt-5 and o-series models use max_completion_tokens; everything else uses max_tokens
        uses_new_params = model_name.startswith(("gpt-5", "o1", "o3", "o4"))
        params = {
            "model": model_name,
            "messages": messages,
            "max_completion_tokens" if uses_new_params else "max_tokens":
                kwargs.get("max_tokens", settings.max_tokens),
            "stream": True
        }

        # o-series and gpt-5 don't support temperature
        if not uses_new_params:
            params["temperature"] = kwargs.get("temperature", settings.temperature)
        
        # Add tools if provided
        if tools:
            params["tools"] = tools
            params["tool_choice"] = kwargs.get("tool_choice", "auto")
        
        logger.info(
            "Starting OpenAI streaming request",
            model=model_name,
            message_count=len(messages),
            has_tools=bool(tools)
        )
        
        try:
            async with performance_timer("openai_stream_completion"):
                stream = await self.client.chat.completions.create(**params)
                
                async for chunk in stream:
                    if chunk.choices[0].delta.content:
                        yield {
                            "type": "content",
                            "data": chunk.choices[0].delta.content
                        }
                    
                    # Handle tool calls in streaming
                    if chunk.choices[0].delta.tool_calls:
                        for tool_call in chunk.choices[0].delta.tool_calls:
                            yield {
                                "type": "tool_call",
                                "data": {
                                    "id": tool_call.id,
                                    "function": {
                                        "name": tool_call.function.name,
                                        "arguments": tool_call.function.arguments
                                    }
                                }
                            }
                    
                    # Handle completion
                    if chunk.choices[0].finish_reason:
                        yield {
                            "type": "done",
                            "data": {
                                "finish_reason": chunk.choices[0].finish_reason,
                                "model": chunk.model
                            }
                        }
        
        except Exception as e:
            logger.error(
                "OpenAI streaming error",
                error=str(e),
                model=model_name,
                exc_info=True
            )
            
            yield {
                "type": "error",
                "data": {"error": str(e)}
            }


class AnthropicService(LLMService):
    """Anthropic Claude service implementation."""
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__("anthropic")
        
        self.api_key = api_key or settings.anthropic_api_key
        if not self.api_key:
            raise LLMServiceError("Anthropic API key not provided", service="anthropic")
        
        self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        self.default_model = "claude-3-sonnet-20240229"
    
    async def complete_chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Complete chat using Anthropic Claude."""
        
        async def _complete():
            model_name = model or self.default_model
            
            # Convert OpenAI format to Anthropic format
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    anthropic_messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Prepare request parameters
            params = {
                "model": model_name,
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", settings.max_tokens),
                "temperature": kwargs.get("temperature", settings.temperature)
            }
            
            if system_message:
                params["system"] = system_message
            
            # Add tools if provided (convert from OpenAI format)
            if tools:
                anthropic_tools = []
                for tool in tools:
                    if tool.get("type") == "function":
                        func = tool["function"]
                        anthropic_tools.append({
                            "name": func["name"],
                            "description": func["description"],
                            "input_schema": func["parameters"]
                        })
                params["tools"] = anthropic_tools
            
            logger.info(
                "Making Anthropic API request",
                model=model_name,
                message_count=len(anthropic_messages),
                has_tools=bool(tools),
                has_system=bool(system_message)
            )
            
            async with performance_timer("anthropic_chat_completion"):
                try:
                    response = await self.client.messages.create(**params)
                    
                    # Extract response data
                    content = ""
                    tool_calls = []
                    
                    for content_block in response.content:
                        if content_block.type == "text":
                            content += content_block.text
                        elif content_block.type == "tool_use":
                            tool_calls.append({
                                "id": content_block.id,
                                "type": "function",
                                "function": {
                                    "name": content_block.name,
                                    "arguments": json.dumps(content_block.input)
                                }
                            })
                    
                    result = {
                        "content": content,
                        "role": "assistant",
                        "tool_calls": tool_calls if tool_calls else None,
                        "usage": {
                            "prompt_tokens": response.usage.input_tokens,
                            "completion_tokens": response.usage.output_tokens,
                            "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                        },
                        "model": response.model,
                        "finish_reason": response.stop_reason
                    }
                    
                    # Record metrics
                    metrics.record_llm_request(
                        service="anthropic",
                        model=model_name,
                        status="success",
                        prompt_tokens=response.usage.input_tokens,
                        completion_tokens=response.usage.output_tokens
                    )
                    
                    logger.info(
                        "Anthropic API request completed",
                        model=model_name,
                        finish_reason=result["finish_reason"],
                        total_tokens=result["usage"]["total_tokens"],
                        has_tool_calls=bool(tool_calls)
                    )
                    
                    return result
                    
                except anthropic.APIError as e:
                    logger.error(
                        "Anthropic API error",
                        error=str(e),
                        status_code=getattr(e, 'status_code', None),
                        exc_info=True
                    )
                    
                    # Record error metrics
                    metrics.record_llm_request(
                        service="anthropic",
                        model=model_name,
                        status="error",
                        prompt_tokens=0,
                        completion_tokens=0
                    )
                    
                    raise LLMServiceError(
                        f"Anthropic API error: {str(e)}",
                        service="anthropic"
                    )
        
        return await self._execute_with_circuit_breaker(_complete)
    
    async def complete_chat_stream(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completion from Anthropic (placeholder - implement when needed)."""
        
        # For now, fall back to non-streaming
        result = await self.complete_chat(messages, tools, model, **kwargs)
        
        # Yield content in chunks to simulate streaming
        content = result.get("content", "")
        chunk_size = 50
        
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            yield {
                "type": "content",
                "data": chunk
            }
            
            # Small delay to simulate streaming
            import asyncio
            await asyncio.sleep(0.01)
        
        # Yield tool calls if present
        if result.get("tool_calls"):
            for tool_call in result["tool_calls"]:
                yield {
                    "type": "tool_call",
                    "data": tool_call
                }
        
        # Yield completion
        yield {
            "type": "done",
            "data": {
                "finish_reason": result.get("finish_reason"),
                "model": result.get("model")
            }
        }


def get_llm_service(service_name: str = "openai") -> LLMService:
    """Get LLM service instance."""
    
    if service_name.lower() == "openai":
        return OpenAIService()
    elif service_name.lower() == "anthropic":
        return AnthropicService()
    else:
        raise ValueError(f"Unsupported LLM service: {service_name}")