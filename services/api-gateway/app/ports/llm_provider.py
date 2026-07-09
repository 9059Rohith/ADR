"""SentinelArena — LLM Provider Port (Interface).

Abstract interface for LLM providers. Implementations include:
- GroqLLMAdapter: Real Groq Llama API calls (LPU inference)
- MockLLMAdapter: Deterministic responses for dev/testing

See ADR-004 for the adapter pattern rationale.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@dataclass
class LLMMessage:
    """A message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = "stop"


class LLMProvider(ABC):
    """Abstract interface for LLM providers.

    All LLM interactions go through this interface, enabling:
    - Mock adapter for testing (no API costs, deterministic)
    - Real adapter for production (Groq LPU Llama 3.3/3.1)
    - Future swappability (OpenAI, Google, etc.)
    """

    @abstractmethod
    async def generate(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a complete response.

        Args:
            messages: Conversation history.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            **kwargs: Provider-specific options.

        Returns:
            Complete LLM response.
        """

    @abstractmethod
    async def stream(
        self,
        messages: list[LLMMessage],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.3,
        system_prompt: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response tokens.

        Args:
            messages: Conversation history.
            max_tokens: Maximum tokens to generate.
            temperature: Sampling temperature.
            system_prompt: Optional system prompt.
            **kwargs: Provider-specific options.

        Yields:
            Response content chunks.
        """

    @abstractmethod
    async def classify(
        self,
        text: str,
        categories: list[str],
        *,
        system_prompt: str | None = None,
    ) -> str:
        """Classify text into one of the given categories.

        Uses the fast/cheap model for cost efficiency.

        Args:
            text: Text to classify.
            categories: List of valid category labels.
            system_prompt: Optional system prompt.

        Returns:
            The selected category label.
        """
