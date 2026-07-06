# ADR-002: PostgreSQL + pgvector Over Dedicated Vector Database

**Status:** Accepted
**Date:** 2025-01-15
**Decision Makers:** SentinelArena Engineering Team

## Context

The RAG pipeline requires vector similarity search for SOP documents and FAQ retrieval. Options:

1. **Dedicated vector DB** (Pinecone, Weaviate, Qdrant, Milvus)
2. **PostgreSQL + pgvector extension**
3. **In-memory vector store** (FAISS, ChromaDB)

## Decision

Use **PostgreSQL with the pgvector extension** for all vector storage and similarity search.

## Rationale

- **Operational simplicity:** One database for relational data (users, venues, incidents, audit log) AND vector data (SOP embeddings). No additional infrastructure to provision, monitor, or secure.
- **Sufficient scale:** Our venue has ~12-15 SOP documents with ~200-500 chunks total. pgvector with an HNSW index handles this comfortably — we're not at the millions-of-vectors scale where dedicated vector DBs shine.
- **ACID compliance:** SOP document updates and their embeddings are transactionally consistent. No eventual-consistency surprises.
- **Cost:** Zero additional cost (pgvector is open-source, included in the postgres:16 Docker image).
- **Async support:** Full compatibility with SQLAlchemy 2.0 async + asyncpg.

## Consequences

- **Pro:** Single backup strategy, single connection pool, single migration tool (Alembic).
- **Pro:** Can use hybrid search (pgvector cosine similarity + PostgreSQL full-text search `tsvector`) for better retrieval quality.
- **Con:** If we scale to millions of documents, we'd need to evaluate a dedicated vector DB. Documented as a future scalability path.
- **Con:** pgvector HNSW index tuning requires some expertise (mitigated: well-documented defaults work for our scale).

## Alternatives Rejected

- **Pinecone/Weaviate:** Unnecessary complexity and cost for <1000 vectors. Would require managing another service, another set of credentials, and cross-service consistency.
- **ChromaDB/FAISS:** In-memory only; no persistence guarantees, no async support, not suitable for multi-instance deployment.
