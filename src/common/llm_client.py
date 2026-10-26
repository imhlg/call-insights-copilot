"""Provider adapters with a small provider-neutral request/response contract."""

import json
import logging
from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from anthropic import Anthropic
from openai import APITimeoutError, OpenAI, Timeout

from config import Settings, settings
from model_router import (
    HAIKU_EFFORT,
    OLLAMA_REQUEST_TIMEOUT_SECONDS,
    Provider,
    ollama_timeout_fallback,
    route_for_task,
)

OLLAMA_REQUEST_TIMEOUT = Timeout(OLLAMA_REQUEST_TIMEOUT_SECONDS, connect=5.0)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int | None
    output_tokens: int | None


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class LLMResult:
    text: str
    finish_reason: str | None
    usage: TokenUsage
    provider: Provider
    model: str
    tool_calls: tuple[ToolCall, ...] = ()


class EmptyModelResponseError(RuntimeError):
    """Raised when a provider finishes without text or a tool call."""


class LLMClient:
    def __init__(
        self,
        config: Settings = settings,
        provider_clients: Mapping[Provider, Any] | None = None,
    ):
        self.config = config
        self._clients: dict[Provider, Any] = dict(provider_clients or {})

    def _get_client(self, provider: Provider) -> Any:
        if provider in self._clients:
            return self._clients[provider]

        if provider == "ollama":
            client = OpenAI(
                base_url=self.config.ollama_base_url,
                api_key="ollama",  # Required by the OpenAI SDK; ignored by Ollama.
            )
        elif provider == "mimo":
            if not self.config.mimo_api_key:
                raise RuntimeError("Set MIMO_API_KEY in .env before running a heavy task.")
            client = OpenAI(
                api_key=self.config.mimo_api_key,
                base_url=self.config.get_mimo_base_url(),
            )
        elif provider == "anthropic":
            if not self.config.anthropic_api_key:
                raise RuntimeError(
                    "Set ANTHROPIC_API_KEY in .env before the Ollama timeout fallback can run."
                )
            client = Anthropic(api_key=self.config.anthropic_api_key)
        else:
            raise RuntimeError(f"Unknown provider {provider!r}.")

        self._clients[provider] = client
        return client

    def complete(
        self,
        *,
        task: str,
        messages: Sequence[Mapping[str, Any]],
        max_output_tokens: int,
        code: str | None = None,
        system: str | None = None,
        escalate: bool = False,
        tools: Sequence[Mapping[str, Any]] | None = None,
        tool_choice: Any = None,
    ) -> LLMResult:
        """Complete a task; use explicit ``code`` or infer size from user messages."""
        if max_output_tokens < 1:
            raise ValueError("max_output_tokens must be at least 1.")

        routing_code = code if code is not None else self._extract_user_text(messages)
        route = route_for_task(task, routing_code, escalate=escalate, config=self.config)
        client = self._get_client(route.provider)
        request: dict[str, Any] = {
            "model": route.model,
            "messages": self._prepare_messages(messages, system),
        }
        if tools is not None:
            request["tools"] = list(tools)
        if tool_choice is not None:
            request["tool_choice"] = tool_choice

        try:
            if route.provider == "mimo":
                response = client.chat.completions.create(
                    **request,
                    max_completion_tokens=max_output_tokens,
                    extra_body={"thinking": {"type": "disabled"}},
                )
            else:
                response = client.chat.completions.create(
                    **request,
                    max_tokens=max_output_tokens,
                    timeout=OLLAMA_REQUEST_TIMEOUT,
                )
        except APITimeoutError:
            if route.provider != "ollama":
                logger.exception(
                    "LLM request failed",
                    extra={"provider": route.provider, "model": route.model, "task": task},
                )
                raise
            logger.warning(
                "Ollama exceeded %s seconds; falling back to Haiku",
                OLLAMA_REQUEST_TIMEOUT_SECONDS,
                extra={"provider": route.provider, "model": route.model, "task": task},
            )
            return self._complete_with_haiku(
                task=task,
                messages=request["messages"],
                max_output_tokens=max_output_tokens,
                tools=tools,
                tool_choice=tool_choice,
            )
        except Exception:
            logger.exception(
                "LLM request failed",
                extra={"provider": route.provider, "model": route.model, "task": task},
            )
            raise

        if not response.choices:
            raise EmptyModelResponseError(
                f"{route.provider} returned no choices for task {task!r}."
            )

        choice = response.choices[0]
        message = choice.message
        text = self._extract_text(getattr(message, "content", None))
        tool_calls = self._extract_tool_calls(getattr(message, "tool_calls", None))
        finish_reason = choice.finish_reason
        if not text.strip() and not tool_calls:
            raise EmptyModelResponseError(
                f"{route.provider} returned no text or tool calls; "
                f"finish_reason={finish_reason!r}. Increase the output-token limit if truncated."
            )

        raw_usage = getattr(response, "usage", None)
        usage = TokenUsage(
            input_tokens=getattr(raw_usage, "prompt_tokens", None),
            output_tokens=getattr(raw_usage, "completion_tokens", None),
        )
        logger.debug(
            "LLM request completed",
            extra={
                "provider": route.provider,
                "model": route.model,
                "task": task,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "finish_reason": finish_reason,
            },
        )
        return LLMResult(
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            provider=route.provider,
            model=route.model,
            tool_calls=tool_calls,
        )

    def _complete_with_haiku(
        self,
        *,
        task: str,
        messages: Sequence[Mapping[str, Any]],
        max_output_tokens: int,
        tools: Sequence[Mapping[str, Any]] | None,
        tool_choice: Any,
    ) -> LLMResult:
        route = ollama_timeout_fallback()
        client = self._get_client(route.provider)
        system, anthropic_messages = self._to_anthropic_messages(messages)
        request: dict[str, Any] = {
            "model": route.model,
            "max_tokens": max_output_tokens,
            "messages": anthropic_messages,
            "output_config": {"effort": HAIKU_EFFORT},
        }
        if system:
            request["system"] = system
        if tools is not None:
            request["tools"] = self._to_anthropic_tools(tools)
        anthropic_tool_choice = self._to_anthropic_tool_choice(tool_choice)
        if anthropic_tool_choice is not None:
            request["tool_choice"] = anthropic_tool_choice

        try:
            response = client.messages.create(**request)
        except Exception:
            logger.exception(
                "Haiku fallback failed",
                extra={"provider": route.provider, "model": route.model, "task": task},
            )
            raise

        text_parts: list[str] = []
        tool_calls: list[ToolCall] = []
        for block in getattr(response, "content", None) or []:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                block_text = getattr(block, "text", "")
                if isinstance(block_text, str):
                    text_parts.append(block_text)
            elif block_type == "tool_use":
                arguments = getattr(block, "input", {})
                if not isinstance(arguments, dict):
                    raise ValueError(
                        f"Tool arguments for {getattr(block, 'name', '')!r} must be a JSON object."
                    )
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=arguments,
                    )
                )
        text = "".join(text_parts)
        finish_reason = getattr(response, "stop_reason", None)
        if not text.strip() and not tool_calls:
            raise EmptyModelResponseError(
                f"{route.provider} returned no text or tool calls; "
                f"finish_reason={finish_reason!r}. Increase the output-token limit if truncated."
            )

        raw_usage = getattr(response, "usage", None)
        usage = TokenUsage(
            input_tokens=getattr(raw_usage, "input_tokens", None),
            output_tokens=getattr(raw_usage, "output_tokens", None),
        )
        logger.debug(
            "LLM request completed",
            extra={
                "provider": route.provider,
                "model": route.model,
                "task": task,
                "input_tokens": usage.input_tokens,
                "output_tokens": usage.output_tokens,
                "finish_reason": finish_reason,
            },
        )
        return LLMResult(
            text=text,
            finish_reason=finish_reason,
            usage=usage,
            provider=route.provider,
            model=route.model,
            tool_calls=tuple(tool_calls),
        )

    @classmethod
    def _to_anthropic_messages(
        cls, messages: Sequence[Mapping[str, Any]]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        system_parts: list[str] = []
        converted: list[dict[str, Any]] = []
        for message in messages:
            role = message.get("role")
            if role == "system":
                system_parts.append(cls._extract_text(message.get("content")))
                continue
            if role == "tool":
                converted.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.get("tool_call_id"),
                                "content": cls._extract_text(message.get("content")),
                            }
                        ],
                    }
                )
                continue
            tool_calls = message.get("tool_calls")
            if role == "assistant" and tool_calls:
                blocks: list[dict[str, Any]] = []
                text = cls._extract_text(message.get("content"))
                if text:
                    blocks.append({"type": "text", "text": text})
                for raw_call in tool_calls:
                    function = raw_call.get("function", {})
                    if not isinstance(function, Mapping):
                        raise ValueError("Assistant tool calls must include a function object.")
                    raw_arguments = function.get("arguments", {})
                    try:
                        arguments = (
                            json.loads(raw_arguments)
                            if isinstance(raw_arguments, str)
                            else raw_arguments
                        )
                    except json.JSONDecodeError as error:
                        raise ValueError(
                            f"Invalid JSON arguments for tool {function.get('name')!r}."
                        ) from error
                    if not isinstance(arguments, dict):
                        raise ValueError(
                            f"Tool arguments for {function.get('name')!r} must be a JSON object."
                        )
                    blocks.append(
                        {
                            "type": "tool_use",
                            "id": raw_call.get("id"),
                            "name": function.get("name"),
                            "input": arguments,
                        }
                    )
                converted.append({"role": "assistant", "content": blocks})
                continue
            converted.append({"role": role, "content": cls._anthropic_content(message.get("content"))})

        merged: list[dict[str, Any]] = []
        for message in converted:
            if merged and merged[-1]["role"] == message["role"] and message["role"] == "user":
                merged[-1]["content"] = cls._content_blocks(merged[-1]["content"]) + cls._content_blocks(
                    message["content"]
                )
            else:
                merged.append(message)
        system = "\n".join(part for part in system_parts if part).strip()
        return system or None, merged

    @classmethod
    def _anthropic_content(cls, content: Any) -> str | list[dict[str, Any]]:
        if isinstance(content, str):
            return content
        blocks = cls._content_blocks(content)
        if len(blocks) == 1 and blocks[0].get("type") == "text":
            return str(blocks[0].get("text", ""))
        return blocks

    @classmethod
    def _content_blocks(cls, content: Any) -> list[dict[str, Any]]:
        if isinstance(content, str):
            return [{"type": "text", "text": content}] if content else []
        if isinstance(content, list):
            return [dict(block) for block in content]
        text = cls._extract_text(content)
        return [{"type": "text", "text": text}] if text else []

    @staticmethod
    def _to_anthropic_tools(tools: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        converted: list[dict[str, Any]] = []
        for tool in tools:
            if tool.get("type") == "function":
                function = tool.get("function", {})
                converted.append(
                    {
                        "name": function.get("name"),
                        "description": function.get("description", ""),
                        "input_schema": function.get("parameters")
                        or {"type": "object", "properties": {}},
                    }
                )
            else:
                converted.append(dict(tool))
        return converted

    @staticmethod
    def _to_anthropic_tool_choice(tool_choice: Any) -> dict[str, str] | None:
        if tool_choice is None:
            return None
        if tool_choice == "auto":
            return {"type": "auto"}
        if tool_choice == "none":
            return {"type": "none"}
        if tool_choice == "required":
            return {"type": "any"}
        if isinstance(tool_choice, Mapping):
            name = tool_choice.get("function", {}).get("name")
            if isinstance(name, str) and name:
                return {"type": "tool", "name": name}
        return {"type": "auto"}

    @staticmethod
    def _prepare_messages(
        messages: Sequence[Mapping[str, Any]], system: str | None
    ) -> list[dict[str, Any]]:
        prepared = [dict(message) for message in messages]
        if system:
            prepared.insert(0, {"role": "system", "content": system})
        return prepared

    @classmethod
    def _extract_user_text(cls, messages: Sequence[Mapping[str, Any]]) -> str:
        return "\n".join(
            cls._extract_text(message.get("content"))
            for message in messages
            if message.get("role") == "user"
        )

    @staticmethod
    def _extract_text(content: Any) -> str:
        if isinstance(content, str):
            return content
        if isinstance(content, (list, tuple)):
            text_parts = []
            for part in content:
                part_type = (
                    part.get("type")
                    if isinstance(part, Mapping)
                    else getattr(part, "type", None)
                )
                part_text = (
                    part.get("text", "")
                    if isinstance(part, Mapping)
                    else getattr(part, "text", "")
                )
                if part_type == "text" and isinstance(part_text, str):
                    text_parts.append(part_text)
            return "".join(text_parts)
        return ""

    @staticmethod
    def _extract_tool_calls(raw_calls: Any) -> tuple[ToolCall, ...]:
        calls: list[ToolCall] = []
        for raw_call in raw_calls or []:
            function = raw_call.function
            raw_arguments = function.arguments
            try:
                arguments = (
                    json.loads(raw_arguments)
                    if isinstance(raw_arguments, str)
                    else raw_arguments
                )
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Provider returned invalid JSON arguments for tool {function.name!r}."
                ) from error
            if not isinstance(arguments, dict):
                raise ValueError(
                    f"Tool arguments for {function.name!r} must be a JSON object."
                )
            calls.append(
                ToolCall(
                    id=raw_call.id,
                    name=function.name,
                    arguments=arguments,
                )
            )
        return tuple(calls)


llm = LLMClient()
