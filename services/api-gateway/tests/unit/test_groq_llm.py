"""SentinelArena — Unit Tests for Groq LLM Adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.adapters.groq_llm import GroqLLMAdapter
from app.ports.llm_provider import LLMMessage, LLMResponse


class TestGroqLLMAdapterInit:
    """Tests for GroqLLMAdapter initialization."""

    def test_init_with_defaults(self) -> None:
        """Test initialization with default settings."""
        with patch("app.adapters.groq_llm.AsyncGroq") as mock_groq:
            adapter = GroqLLMAdapter(api_key="test-key")
            assert adapter._api_key == "test-key"
            assert adapter._default_model == "llama-3.3-70b-versatile"
            assert adapter._fast_model == "llama-3.1-8b-instant"
            mock_groq.assert_called_once_with(api_key="test-key")

    def test_format_messages_with_system(self) -> None:
        """Test formatting messages with system prompt."""
        with patch("app.adapters.groq_llm.AsyncGroq"):
            adapter = GroqLLMAdapter(api_key="test-key")
            messages = [LLMMessage(role="user", content="Hello")]
            formatted = adapter._format_messages(messages, system="Be helpful")
            assert len(formatted) == 2
            assert formatted[0] == {"role": "system", "content": "Be helpful"}
            assert formatted[1] == {"role": "user", "content": "Hello"}


@pytest.mark.asyncio
class TestGroqLLMAdapterGenerate:
    """Tests for generation methods."""

    async def test_generate_success(self) -> None:
        """Test successful completion generation."""
        with patch("app.adapters.groq_llm.AsyncGroq") as mock_groq_cls:
            mock_client = MagicMock()
            mock_groq_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Groq response"
            mock_response.usage.prompt_tokens = 10
            mock_response.usage.completion_tokens = 5
            mock_response.usage.total_tokens = 15

            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            adapter = GroqLLMAdapter(api_key="test-key")
            res = await adapter.generate(
                [LLMMessage(role="user", content="Hi")],
                model="llama-3.3-70b-versatile",
            )

            assert isinstance(res, LLMResponse)
            assert res.content == "Groq response"
            assert res.model == "llama-3.3-70b-versatile"
            assert res.usage["total_tokens"] == 15


@pytest.mark.asyncio
class TestGroqLLMAdapterClassify:
    """Tests for fast classification."""

    async def test_classify_match(self) -> None:
        """Test exact category matching."""
        with patch("app.adapters.groq_llm.AsyncGroq") as mock_groq_cls:
            mock_client = MagicMock()
            mock_groq_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "navigation"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            adapter = GroqLLMAdapter(api_key="test-key")
            cat = await adapter.classify("where is gate 1?", ["navigation", "crowd", "decision"])
            assert cat == "navigation"

    async def test_classify_fallback(self) -> None:
        """Test fallback when LLM returns unexpected text."""
        with patch("app.adapters.groq_llm.AsyncGroq") as mock_groq_cls:
            mock_client = MagicMock()
            mock_groq_cls.return_value = mock_client

            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "something random"
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            adapter = GroqLLMAdapter(api_key="test-key")
            cat = await adapter.classify("test", ["navigation", "crowd"])
            assert cat == "navigation"  # Fallback to first category
