"""Prompt builder — assembles system prompts with context."""

from __future__ import annotations


class PromptBuilder:
    """Builds system prompts by combining base template with context."""

    def __init__(self, base_prompt: str = "") -> None:
        self.base_prompt = base_prompt

    def build(
        self,
        *,
        memory_context: list[str] | None = None,
        knowledge_context: list[str] | None = None,
    ) -> str:
        """Build the complete system prompt."""
        parts = [self.base_prompt]

        if memory_context:
            parts.append("\n## 相关记忆")
            for snippet in memory_context:
                parts.append(f"- {snippet}")

        if knowledge_context:
            parts.append("\n## 相关知识")
            for snippet in knowledge_context:
                parts.append(f"- {snippet}")

        return "\n".join(parts)
