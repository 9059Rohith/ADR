# ADR-004: Mock Adapter Pattern for External APIs

**Status:** Accepted
**Date:** 2025-01-15
**Decision Makers:** SentinelArena Engineering Team

## Context

The system depends on external APIs (Anthropic Claude, Weather API, IoT sensor feeds) that may be unavailable during development, testing, or demo environments. We need a strategy for handling these dependencies gracefully.

## Decision

Implement a **Ports and Adapters (Hexagonal Architecture)** pattern where every external dependency is accessed through an abstract interface (port), with both real and mock implementations (adapters).

## Rationale

- **Zero-config development:** Developers can run the full stack locally without any API keys. The mock adapters return realistic, deterministic responses.
- **Reliable testing:** Unit and integration tests use mock adapters by default, ensuring tests are fast, deterministic, and don't incur API costs.
- **Transparent to judges:** Each mock adapter is explicitly documented with a "MOCK" label and explains what real data would look like. This honesty about what's simulated vs. real strengthens credibility.
- **Swap-in simplicity:** Switching from mock to real requires only setting an environment variable (e.g., `ANTHROPIC_API_KEY`). No code changes needed.
- **Cost control:** Prevents accidental LLM API charges during development and CI runs.

## Implementation

```python
# Port (interface)
class LLMProvider(Protocol):
    async def generate(self, prompt: str, **kwargs) -> str: ...
    async def stream(self, prompt: str, **kwargs) -> AsyncIterator[str]: ...

# Real adapter
class AnthropicLLMAdapter:
    def __init__(self, api_key: str, model: str): ...

# Mock adapter
class MockLLMAdapter:
    """Returns deterministic, realistic responses for development/testing."""
    async def generate(self, prompt: str, **kwargs) -> str:
        return self._lookup_response(prompt)

# Factory
def create_llm_provider() -> LLMProvider:
    if os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicLLMAdapter(...)
    return MockLLMAdapter()
```

## Consequences

- **Pro:** Development, testing, and demo environments all work without external dependencies.
- **Pro:** Clear separation of concerns; business logic never directly depends on a specific API client.
- **Con:** Mock adapters must be maintained to stay realistic. Mitigated by keeping mocks simple and documenting their limitations.

## Alternatives Rejected

- **VCR/recorded cassettes:** Only works for deterministic request/response patterns; LLM outputs vary too much.
- **Always-real API calls:** Expensive, flaky in CI, blocks development without keys.
