"""SentinelArena — Groq LLM Adapter.

Implements the LLMProvider interface using Groq's ultra-fast LPU inference engine
with Llama 3.3 70B Versatile (for complex reasoning) and Llama 3.1 8B Instant (for fast routing/classification).

Provides:
- Synchronous and asynchronous completion generation
- Real-time token streaming
- Intent classification and routing
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from typing import Any

from groq import AsyncGroq
from groq.types.chat import ChatCompletion

from app.config import get_settings
from app.ports.llm_provider import LLMMessage, LLMProvider, LLMResponse

logger = logging.getLogger(__name__)


class GroqLLMAdapter:
    """LLM provider implementation using Groq API."""

    def __init__(self, api_key: str | None = None, default_model: str | None = None) -> None:
        """Initialize Groq client.

        Args:
            api_key: Groq API key. If not provided, loaded from settings.
            default_model: Default completion model to use.
        """
        settings = get_settings()
        self._api_key = api_key or settings.groq_api_key
        self._client = AsyncGroq(api_key=self._api_key)
        self._default_model = default_model or settings.groq_reasoning_model
        self._fast_model = settings.groq_fast_model
        logger.info(
            "Groq LLM adapter initialized",
            reasoning_model=self._default_model,
            fast_model=self._fast_model,
        )

    def _format_messages(
        self,
        messages: list[LLMMessage],
        system: str | None = None,
    ) -> list[dict[str, str]]:
        """Format messages for the Groq chat completion API."""
        formatted: list[dict[str, str]] = []

        if system:
            formatted.append({"role": "system", "content": system})

        for msg in messages:
            formatted.append({"role": msg.role, "content": msg.content})

        return formatted

    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response using Groq chat completion API.

        Args:
            messages: Conversation history.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: System prompt.
            model: Model to use (defaults to Llama 3.3 70B Versatile).
            **kwargs: Additional arguments.

        Returns:
            LLMResponse with generated text and usage statistics.
        """
        model_name = model or self._default_model
        system = system_prompt or kwargs.get("system")
        formatted_messages = self._format_messages(messages, system)

        try:
            response: ChatCompletion = await self._client.chat.completions.create(
                messages=formatted_messages,  # type: ignore[arg-type]
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
            )

            content = response.choices[0].message.content or ""
            usage: dict[str, int] = {}
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(
                "Groq completion generated: model=%s tokens=%s",
                model_name,
                usage.get("total_tokens", 0),
            )

            return LLMResponse(
                content=content,
                model=model_name,
                usage=usage,
            )
        except Exception as exc:
            logger.error("Groq API error during generate: %s (model=%s)", exc, model_name)
            raise

    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """Stream a response token-by-token using Groq LPU inference.

        Args:
            messages: Conversation history.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: System prompt.
            model: Model to use.
            **kwargs: Additional arguments.

        Yields:
            Text chunks as they are generated.
        """
        model_name = model or self._default_model
        system = system_prompt or kwargs.get("system")
        formatted_messages = self._format_messages(messages, system)

        try:
            stream_response = await self._client.chat.completions.create(
                messages=formatted_messages,  # type: ignore[arg-type]
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream_response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as exc:
            logger.error("Groq API error during stream: %s (model=%s)", exc, model_name)
            raise

    async def classify(
        self,
        text: str,
        categories: list[str],
        *,
        system_prompt: str | None = None,
        model: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Classify input into one of several categories using fast model.

        Uses Llama 3.1 8B Instant by default for ultra-low latency routing.

        Args:
            text: Text to classify.
            categories: Possible category labels.
            system_prompt: Optional custom system instructions.
            model: Model to use (defaults to fast routing model).
            **kwargs: Additional arguments.

        Returns:
            The matching category name.
        """
        model_name = model or self._fast_model
        categories_str = ", ".join(f'"{c}"' for c in categories)

        base_sys = (
            f"You are a precise classification engine. Classify the user's input into exactly one of these categories: {categories_str}. "
            "Return ONLY the category name as your entire response. Do not include quotes, punctuation, or explanation."
        )
        sys_content = f"{system_prompt}\n\n{base_sys}" if system_prompt else base_sys

        messages = [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": text},
        ]

        try:
            response = await self._client.chat.completions.create(
                messages=messages,  # type: ignore[arg-type]
                model=model_name,
                max_tokens=50,
                temperature=0.1,
            )

            result = (response.choices[0].message.content or "").strip().lower()

            # Exact or substring match against valid categories
            for category in categories:
                if category.lower() in result:
                    return category

            logger.warning(
                "Groq classification returned unmatched result '%s', defaulting to '%s'",
                result,
                categories[0] if categories else "general",
            )
            return categories[0] if categories else "general"
        except Exception as exc:
            logger.error("Groq API error during classify: %s", exc)
            return categories[0] if categories else "general"


