"""OpenAI-compatible LLM provider (covers OpenAI, DeepSeek, Qwen, etc.)."""

from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from kore.llm.base import ChatResponse, LLMProvider, TokenUsage, ToolCall


class OpenAIProvider(LLMProvider):
    """Provider for OpenAI and compatible APIs."""

    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        self.client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-4o",
        **kwargs: Any,
    ) -> ChatResponse:
        thinking = kwargs.pop("thinking", None)
        extra_body = kwargs.pop("extra_body", None) or {}
        if thinking is not None:
            extra_body["thinking"] = {"type": thinking}

        params: dict[str, Any] = {"model": model, "messages": messages, **kwargs}
        if tools:
            params["tools"] = tools
        if extra_body:
            params["extra_body"] = extra_body

        response = await self.client.chat.completions.create(**params)
        choice = response.choices[0]

        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=tc.function.arguments,
                )
                for tc in choice.message.tool_calls
            ]

        return ChatResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
            model=response.model,
            finish_reason=choice.finish_reason or "",
        )

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str = "gpt-4o",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        thinking = kwargs.pop("thinking", None)
        extra_body = kwargs.pop("extra_body", None) or {}
        if thinking is not None:
            extra_body["thinking"] = {"type": thinking}

        params: dict[str, Any] = {"model": model, "messages": messages, "stream": True, **kwargs}
        if tools:
            params["tools"] = tools
        if extra_body:
            params["extra_body"] = extra_body

        stream = await self.client.chat.completions.create(**params)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
