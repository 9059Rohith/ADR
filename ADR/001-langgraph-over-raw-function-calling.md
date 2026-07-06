# ADR-001: LangGraph Over Raw Function Calling

**Status:** Accepted
**Date:** 2025-01-15
**Decision Makers:** SentinelArena Engineering Team

## Context

We need a multi-agent orchestration framework for four specialized AI agents (Crowd, Navigation, Decision, Language). Options considered:

1. **Raw LLM function calling** — single model with tools
2. **LangGraph** — structured graph-based agent orchestration
3. **CrewAI / AutoGen** — higher-level multi-agent frameworks

## Decision

Use **LangGraph** with a manual supervisor pattern (not the helper library).

## Rationale

- **Structured state management:** LangGraph's `TypedDict` state enables clear data flow between agents without prompt pollution.
- **Deterministic routing:** Critical paths (pathfinding, density thresholds) must be deterministic. LangGraph lets us mix deterministic nodes with LLM-powered nodes in the same graph.
- **Human-in-the-loop:** LangGraph's `interrupt` mechanism natively supports the operator approval step required for the Decision Agent.
- **Debuggability:** Graph visualization and step-by-step execution traces make it possible to audit every decision path — essential for the cited-recommendation requirement.
- **Production readiness:** Unlike higher-level frameworks (CrewAI, AutoGen), LangGraph doesn't impose opinionated agent loops that can cause runaway token usage.

## Consequences

- **Pro:** Full control over agent orchestration, explicit state transitions, built-in checkpointing.
- **Pro:** Easy to add new agents or modify routing without restructuring.
- **Con:** More boilerplate than high-level frameworks; we must manually implement the supervisor routing.
- **Con:** Requires Python expertise for the orchestration layer (mitigated: our entire backend is Python).

## Alternatives Rejected

- **Raw function calling:** No state management, no graph structure, hard to implement multi-agent hand-offs and human-in-the-loop.
- **CrewAI:** Too opinionated, limited control over execution flow, not production-proven at our required reliability level.
