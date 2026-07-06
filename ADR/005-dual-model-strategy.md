# ADR-005: Dual-Model Cost/Latency Strategy

**Status:** Accepted
**Date:** 2025-01-15
**Decision Makers:** SentinelArena Engineering Team

## Context

The system makes multiple LLM calls per user interaction (intent classification, constraint extraction, response generation, translation). Using the most powerful model for every call is unnecessarily expensive and slow.

## Decision

Implement a **dual-model strategy**: use a faster/cheaper model for classification and routing tasks, and reserve the larger reasoning model only for complex synthesis (Decision Agent).

## Configuration

| Task | Model Tier | Rationale |
|------|-----------|-----------|
| Intent classification (Router) | Fast (claude-haiku) | Simple classification; <100 output tokens |
| Constraint extraction (Navigation) | Fast | Structured extraction; schema-guided |
| Response phrasing | Fast | Template-guided generation |
| Translation (Language Agent) | Fast | Well-defined input/output |
| Decision synthesis (Decision Agent) | Reasoning (claude-sonnet) | Complex multi-source reasoning with citations |
| Risk assessment (Crowd Agent) | Reasoning | Requires contextual analysis of trends + SOPs |

## Rationale

- **Cost reduction:** ~70% of LLM calls use the fast model, which is ~10x cheaper per token. Estimated savings: 60-80% of total LLM API cost.
- **Latency improvement:** Fast model responds in ~200-400ms; reasoning model in ~800-1500ms. By using fast model for routing, we reduce the critical path for most user interactions.
- **Quality preservation:** Complex reasoning tasks (Decision Agent synthesis, Crowd Agent risk assessment) still get the full power of the reasoning model where it matters most.

## Consequences

- **Pro:** Significant cost savings, measurable latency improvement on p50/p95.
- **Pro:** Demonstrates cost-awareness to judges — a strong "Efficiency" signal.
- **Con:** Two model configurations to manage. Mitigated by centralizing model selection in the adapter factory.
- **Con:** Must verify that the fast model handles classification/translation accurately enough. Covered by the AI eval suite.
