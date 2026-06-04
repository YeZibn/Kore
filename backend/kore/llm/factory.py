"""LLM provider factory."""

from __future__ import annotations

from kore.config import LLMProviderConfig
from kore.llm.base import LLMProvider
from kore.llm.openai_provider import OpenAIProvider


class LLMFactory:
    """Factory for creating LLM provider instances."""

    def __init__(self, config: LLMProviderConfig) -> None:
        self.config = config

    def create(self, model: str) -> LLMProvider:
        """Create an LLM provider based on model name."""
        model_lower = model.lower()

        if "deepseek" in model_lower:
            return OpenAIProvider(
                api_key=self.config.deepseek_api_key,
                base_url=self.config.deepseek_base_url,
            )

        if "qwen" in model_lower:
            return OpenAIProvider(
                api_key=self.config.qwen_api_key,
                base_url=self.config.qwen_base_url,
            )

        if "gpt" in model_lower or "o1" in model_lower or "o3" in model_lower or "o4" in model_lower:
            return OpenAIProvider(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_base_url,
            )

        # Default: OpenAI-compatible
        return OpenAIProvider(
            api_key=self.config.openai_api_key,
            base_url=self.config.openai_base_url,
        )
