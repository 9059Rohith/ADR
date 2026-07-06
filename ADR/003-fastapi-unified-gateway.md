# ADR-003: Unified FastAPI Gateway

**Status:** Accepted
**Date:** 2025-01-15
**Decision Makers:** SentinelArena Engineering Team

## Context

The system needs an API gateway handling authentication, rate limiting, request validation, and routing to backend services. Options:

1. **Node.js (Express/Fastify)** gateway + Python AI services
2. **Unified FastAPI** gateway incorporating all backend logic
3. **API Gateway service** (Kong, AWS API Gateway) + microservices

## Decision

Use a **unified FastAPI gateway** that handles HTTP routing, auth, validation, and directly integrates with the LangGraph agent orchestrator.

## Rationale

- **Language consistency:** The agent orchestrator (LangGraph), RAG pipeline, and density evaluator are all Python. A unified Python backend eliminates inter-service serialization overhead and simplifies deployment.
- **Async-native:** FastAPI with `asyncpg` and `aiohttp` provides fully non-blocking I/O across all paths — DB queries, LLM API calls, WebSocket connections, and Redis operations.
- **SSE/WebSocket support:** FastAPI's `StreamingResponse` and WebSocket support enable efficient real-time streaming without additional proxy layers.
- **Simplified deployment:** One Docker container for all backend logic (gateway + orchestrator), reducing operational complexity for a hackathon submission.
- **Pydantic v2 integration:** FastAPI's native Pydantic v2 integration means request/response validation schemas double as documentation (OpenAPI/Swagger auto-generation).

## Consequences

- **Pro:** Single codebase, single test suite, single deployment artifact for the backend.
- **Pro:** No inter-service latency for gateway-to-orchestrator communication.
- **Con:** Tighter coupling between gateway and AI logic. Mitigated by hexagonal architecture (ports/adapters) so the orchestrator is logically separated.
- **Con:** Cannot independently scale gateway vs. orchestrator. Acceptable at hackathon scale; documented as a future decomposition path.

## Alternatives Rejected

- **Node.js gateway:** Would require maintaining two backend languages, JSON serialization between services, and duplicate auth logic.
- **Kong/AWS API Gateway:** Over-engineered for this deployment model. Adds operational complexity without proportional benefit at our scale.
