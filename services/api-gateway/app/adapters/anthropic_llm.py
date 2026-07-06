"""SentinelArena — Anthropic Claude LLM Adapter.

Real LLM adapter that calls the Anthropic Claude API.
Implements the LLMProvider port interface.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from typing import Any

import anthropic

from app.ports.llm_provider import LLMMessage, LLMProvider, LLMResponse


class AnthropicLLMAdapter(LLMProvider):
    """Anthropic Claude API adapter.

    Supports both synchronous generation and streaming.
    Uses the async Anthropic client for non-blocking I/O.
    """

    def __init__(self, api_key: str, model: str) -> None:
        """Initialize the Anthropic adapter.

        Args:
            api_key: Anthropic API key.
            model: Model identifier (e.g., 'claude-sonnet-4-20250514').
        """
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete response via the Claude API."""
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"
        ]

        create_kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
        }

        if system_prompt:
            create_kwargs["system"] = system_prompt

        response = await self._client.messages.create(**create_kwargs)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason or "stop",
        )

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response tokens via the Claude API."""
        anthropic_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
            if msg.role != "system"
        ]

        create_kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": anthropic_messages,
        }

        if system_prompt:
            create_kwargs["system"] = system_prompt

        async with self._client.messages.stream(**create_kwargs) as stream:
            async for text in stream.text_stream:
                yield text

    async def classify(
        self,
        text: str,
        categories: list[str],
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Classify text into one of the given categories using Claude."""
        categories_str = ", ".join(categories)
        classification_prompt = (
            f"Classify the following text into exactly ONE of these categories: "
            f"{categories_str}\n\n"
            f"Text: {text}\n\n"
            f"Respond with ONLY the category name, nothing else."
        )

        response = await self.generate(
            messages=[LLMMessage(role="user", content=classification_prompt)],
            max_tokens=50,
            temperature=0.0,
            system_prompt=system_prompt or "You are a text classifier. Respond with only the category name.",
        )

        # Normalize the response to match one of the categories
        result = response.content.strip().lower()
        for cat in categories:
            if cat.lower() in result:
                return cat

        return categories[0]  # Fallback to first category
