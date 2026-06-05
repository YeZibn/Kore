"""Agent core — the main ReAct reasoning loop."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from kore.config import KoreConfig
from kore.llm.base import LLMProvider, ToolCall
from kore.llm.factory import LLMFactory
from kore.prompting.builder import PromptBuilder
from kore.runtime.models import ModelState, RunContext, RunMode, RunStatus
from kore.tools.base import ToolResult
from kore.tools.builtin_tools import get_builtin_tools
from kore.tools.decorator import get_definition
from kore.tools.executor import ToolExecutor
from kore.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class AgentCore:
    """Main agent that runs the ReAct reasoning loop."""

    def __init__(self, config: KoreConfig, model_state: ModelState | None = None) -> None:
        self.config = config
        self.model_state = model_state or ModelState(current_model=config.agent.chat_model)
        self.llm_factory = LLMFactory(config.llm)
        self.tool_registry = ToolRegistry()
        self.prompt_builder = PromptBuilder(config.system_prompt)

        # Register built-in tools
        self._register_builtin_tools()

        # Create executor
        self.tool_executor = ToolExecutor(
            self.tool_registry,
            retry_count=config.agent.tool_retry_count,
        )

    def _register_builtin_tools(self) -> None:
        """Register all built-in tools."""
        for tool_fn in get_builtin_tools():
            definition = get_definition(tool_fn)
            self.tool_registry.register(definition)

    async def run(self, message: str, session_id: str = "") -> str:
        """Process a user message and return a response using Direct mode (ReAct loop)."""
        ctx = RunContext(run_id=str(uuid.uuid4()), user_message=message)

        logger.info("Run %s: mode=direct, message=%s...", ctx.run_id, message[:50])

        try:
            reply = await self._run_direct(message, ctx)
            ctx.status = RunStatus.COMPLETED
            logger.info(
                "Run %s: completed, tokens=%d, tool_calls=%d",
                ctx.run_id, ctx.total_tokens, ctx.total_tool_calls,
            )
            return reply
        except Exception as e:
            ctx.status = RunStatus.FAILED
            logger.error("Run %s: failed with error: %s", ctx.run_id, e)
            raise

    async def _run_direct(self, message: str, ctx: RunContext) -> str:
        """Direct mode: simple ReAct loop.

        Flow:
            1. Build messages (system + user)
            2. Get tool schemas
            3. Call LLM
            4. If tool_calls → execute tools → append results → go to 3
            5. If no tool_calls → return content as reply
        """
        # Build initial messages
        system_prompt = self.prompt_builder.build()
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ]

        # Get tool schemas
        tools = self.tool_registry.get_schemas() or None

        # Get LLM provider — use runtime model state
        model = self.model_state.current_model
        llm = self.llm_factory.create(model)
        llm_kwargs: dict[str, Any] = {}
        if "deepseek" in model.lower():
            llm_kwargs["thinking"] = (
                "enabled" if self.config.llm.deepseek_thinking_enabled else "disabled"
            )

        # ReAct loop
        max_steps = self.config.agent.max_direct_steps
        for step in range(max_steps):
            logger.debug("Run %s: step %d, model=%s", ctx.run_id, step, model)

            response = await llm.chat(
                messages=messages,
                tools=tools,
                model=model,
                **llm_kwargs,
            )

            # Track usage
            ctx.total_tokens += response.usage.total_tokens

            # If no tool calls, this is the final reply
            if not response.tool_calls:
                return response.content

            # Append assistant message with tool calls
            assistant_msg: dict[str, Any] = {"role": "assistant", "content": response.content or None}
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments},
                }
                for tc in response.tool_calls
            ]
            messages.append(assistant_msg)

            # Execute tool calls
            tool_results = await self.tool_executor.execute(response.tool_calls)
            ctx.total_tool_calls += len(tool_results)

            # Append tool results to messages
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "tool_call_id": result.call_id,
                    "content": result.output,
                })

        # Max steps reached — ask LLM for final answer without tools
        logger.warning("Run %s: max steps (%d) reached", ctx.run_id, max_steps)
        messages.append({
            "role": "user",
            "content": "请根据以上信息给出最终回复。",
        })
        response = await llm.chat(messages=messages, model=model, **llm_kwargs)
        ctx.total_tokens += response.usage.total_tokens
        return response.content
