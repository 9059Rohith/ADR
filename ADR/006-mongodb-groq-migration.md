# ADR-006: Migration to MongoDB Atlas & Groq LPU Inference

**Status:** Accepted (Supersedes ADR-002 and updates ADR-005 provider selection)  
**Date:** 2026-07-06  
**Decision Makers:** SentinelArena Engineering Team & User  

## Context

To achieve top 1% real-time performance, ultra-low latency response times, and seamless cloud-native scalability for smart stadium operations, the platform required re-evaluating its foundational AI inference engine and database storage layer.

Previously, the system relied on:
1. **Anthropic Claude** for agent reasoning and classification.
2. **PostgreSQL + pgvector** (via SQLAlchemy ORM) for relational and vector storage.

While functional, real-time emergency triage and dynamic crowd management during 10,000+ attendee stadium events demand sub-second inference latency and flexible, document-oriented hierarchical data structures (stadium graphs, zones, incident logs, and SOP knowledge bases).

## Decision

We have decided to migrate our core infrastructure to:
1. **AI Provider:** **Groq LPU Inference Engine**, utilizing:
   - **Llama 3.3 70B Versatile** for complex multi-source decision synthesis and RAG triage.
   - **Llama 3.1 8B Instant** for ultra-fast intent classification, routing, and multilingual translation.
2. **Database Layer:** **MongoDB Atlas**, utilizing:
   - **Motor (`AsyncIOMotorClient`)** for non-blocking asynchronous I/O.
   - **Pydantic v2 (`MongoDoc` schemas)** for clean document serialization and validation.
   - **MongoDB Atlas Vector Search (`$vectorSearch`)** for RAG knowledge retrieval and text search.

## Rationale

- **Instantaneous AI Inference (Groq LPU):** Groq's Language Processing Units (LPUs) deliver ~300+ tokens/second. For stadium safety and emergency evacuation advisories, this 10x reduction in latency directly impacts crowd safety and operator decision speed.
- **Document Model Alignment (MongoDB):** Stadium layouts (nodes, edges, floors, zones) and incident reports are inherently hierarchical and JSON-like. MongoDB eliminates ORM impedance mismatch, simplifying schema evolution as tournament requirements change.
- **Unified Vector & Document Store (Atlas):** MongoDB Atlas Vector Search allows storing SOP documents, metadata, and vector embeddings in a single collection with native indexing, removing the need for external vector databases or SQL extensions.
- **Asynchronous Efficiency:** Motor integrates natively with FastAPI's `asyncio` event loop and lifespan management, supporting high-concurrency match-day traffic without thread blocking.
- **Automated Demo Readiness:** Automated database seeding (`seed_mongodb`) populates demo users, venue layouts, POIs, and SOP documents instantly on startup when collections are empty.

## Consequences

### Positive
- **Pro:** Sub-second agent routing and decision generation.
- **Pro:** Simplified data layer without Alembic migration overhead or SQL join complexity.
- **Pro:** Built-in rate limiting and OWASP security headers protect high-throughput API endpoints.
- **Pro:** Fully cloud-ready and deployable to container platforms (Docker, Cloud Run, Kubernetes) with zero code changes.

### Negative / Mitigations
- **Con:** Requires active MongoDB Atlas cluster and Groq API key in production environment variables.
  - *Mitigation:* Clear `.env.example`, automated fallback to in-memory/demo mode when offline, and detailed deployment documentation.

## Alternatives Rejected

- **Staying on PostgreSQL + SQLAlchemy:** The relational schema required complex joins for venue graphs and POIs, and ORM session management introduced unnecessary overhead for high-frequency crowd updates.
- **OpenAI / Anthropic Direct:** Higher latency per token compared to Groq LPU inference, which is critical for real-time emergency response and crowd routing.
