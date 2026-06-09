"""LLM provider abstraction layer."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class ToolCall:
    """A tool call requested by the LLM."""

    id: str
    name: str
    arguments: str  # JSON string from the LLM


@dataclass
class TokenUsage:
    """Token usage statistics."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class ChatResponse:
    """Response from an LLM chat call."""

    content: str
    tool_calls: list[ToolCall] | None = None
    reasoning_content: str = ""
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""
    finish_reason: str = ""


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    name: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str = "",
        **kwargs: Any,
    ) -> ChatResponse:
        """Send a chat completion request."""
        ...

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        model: str = "",
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Send a streaming chat completion request. Override in subclasses."""
        raise NotImplementedError(f"{self.name} does not support streaming")

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts."""
        raise NotImplementedError(f"{self.name} does not support embeddings")
