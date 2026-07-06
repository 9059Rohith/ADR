"""SentinelArena — Adapters module init.

Factory functions for creating adapter instances based on configuration.
"""

from __future__ import annotations

from app.config import get_settings
from app.ports.llm_provider import LLMProvider


def create_llm_provider(*, use_fast_model: bool = False) -> LLMProvider:
    """Factory: create LLM provider based on configuration.

    If ANTHROPIC_API_KEY is set, creates a real Claude adapter.
    Otherwise, creates a mock adapter for development/testing.

    Args:
        use_fast_model: If True, use the faster/cheaper model for
                       classification and routing tasks.

    Returns:
        An LLM provider instance.
    """
    settings = get_settings()

    if settings.use_real_llm:
        from app.adapters.anthropic_llm import AnthropicLLMAdapter

        model = (
            settings.anthropic_fast_model if use_fast_model
            else settings.anthropic_reasoning_model
        )
        return AnthropicLLMAdapter(
            api_key=settings.anthropic_api_key,
            model=model,
        )

    from app.adapters.mock_llm import MockLLMAdapter
    return MockLLMAdapter()
