# SentinelArena — Feature Traceability Matrix

> Maps every implemented feature back to the problem statement to demonstrate alignment.

## Problem Statement Requirements

The challenge brief specifies four core requirements for a "Smart Stadiums & Tournament Operations" platform:

1. **Dynamic Crowd Management** — real-time crowd monitoring, density analysis, predictive alerts
2. **Smart Indoor Navigation** — wayfinding, accessibility-aware routing, natural-language queries
3. **Real-Time Decision Support** — multi-source data fusion, cited recommendations, human-in-the-loop
4. **Multi-Language Assistance** — multilingual support, voice I/O, cultural adaptation

---

## Traceability Matrix

### 1. Dynamic Crowd Management → §2.1

| Feature | Implementation | GenAI-Native? | Files |
|---------|---------------|---------------|-------|
| Per-zone density ingestion (5s intervals) | Crowd Simulator → Redis Streams → API Gateway | No (infrastructure) | `services/crowd-simulator/` |
| EWMA trend forecasting | Deterministic density evaluator | No (statistical) | `services/api-gateway/app/core/density_evaluator.py` |
| LLM risk assessment | Crowd Agent reasons over trends + SOPs | **Yes** — LLM contextualizes numeric data into actionable risk language | `services/api-gateway/app/agents/crowd_agent.py` |
| Natural-language advisories | Crowd Agent generates human-readable alerts | **Yes** — would be template-only without LLM | `services/api-gateway/app/agents/crowd_agent.py` |
| Real-time heatmap overlay | WebSocket → Dashboard SVG map | No (visualization) | `apps/web-dashboard/` |
| Fan rerouting suggestions | Personalized GenAI rerouting per user context | **Yes** — adapts to individual fan's location/preferences | `services/api-gateway/app/agents/crowd_agent.py` |

### 2. Smart Indoor Navigation → §2.2

| Feature | Implementation | GenAI-Native? | Files |
|---------|---------------|---------------|-------|
| Venue graph model | PostgreSQL nodes/edges with accessibility metadata | No (data structure) | `services/api-gateway/app/models/venue.py` |
| Dijkstra/A* pathfinding | Deterministic algorithm with congestion weighting | No (algorithm) | `services/api-gateway/app/core/pathfinding.py` |
| Natural-language query parsing | Navigation Agent extracts intent + constraints via LLM | **Yes** — understands "nearest accessible restroom avoiding stairs" | `services/api-gateway/app/agents/navigation_agent.py` |
| Turn-by-turn instruction generation | LLM phrases route JSON into natural language | **Yes** — generates contextual, human-friendly directions | `services/api-gateway/app/agents/navigation_agent.py` |
| Interactive indoor map | SVG with route overlay + congestion colors | No (visualization) | `apps/fan-pwa/` |
| Voice input/output | Web Speech API for hands-free navigation | No (browser API) | `apps/fan-pwa/` |

### 3. Real-Time Decision Support → §2.3

| Feature | Implementation | GenAI-Native? | Files |
|---------|---------------|---------------|-------|
| Multi-source data fusion | Decision Agent fuses crowd + incidents + weather + SOPs | **Yes** — LLM synthesizes disparate data sources | `services/api-gateway/app/agents/decision_agent.py` |
| RAG over SOP documents | pgvector similarity search + LLM reasoning | **Yes** — retrieval + LLM synthesis is core RAG | `services/api-gateway/app/agents/decision_agent.py` |
| Cited recommendations | Every recommendation cites source (Crowd Agent, SOP §X) | **Yes** — citation generation is LLM-native | `services/api-gateway/app/agents/decision_agent.py` |
| Human-in-the-loop approval | Operators approve/reject/edit before broadcast | No (workflow) | `services/api-gateway/app/routes/decisions.py` |
| Audit logging | Immutable log of all decisions + outcomes | No (compliance) | `services/api-gateway/app/models/audit_log.py` |

### 4. Multi-Language Assistance → §2.4

| Feature | Implementation | GenAI-Native? | Files |
|---------|---------------|---------------|-------|
| Locale-aware translation | Language Agent translates all dynamic content | **Yes** — LLM handles nuanced translation + tone | `services/api-gateway/app/agents/language_agent.py` |
| Cultural tone adjustment | System prompt includes cultural context per locale | **Yes** — culturally appropriate communication | `services/api-gateway/app/agents/language_agent.py` |
| 5 language support | EN, HI, TA, TE, ES | **Yes** (dynamic content) / No (static i18n) | Config + i18n files |
| Voice input (STT) | Web Speech API | No (browser API) | `apps/fan-pwa/` |
| Voice output (TTS) | Web Speech API | No (browser API) | `apps/fan-pwa/` |
| Static UI i18n | react-i18next with translation files | No (i18n framework) | `apps/*/src/i18n/` |

---

## What's GenAI-Native vs. Supporting Infrastructure

### GenAI-Native (would be materially worse or impossible without an LLM)
- Natural-language query understanding (Navigation Agent)
- Contextual risk assessment with SOP precedent (Crowd Agent)
- Multi-source synthesis with citations (Decision Agent)
- Locale-aware translation with cultural tone (Language Agent)
- Turn-by-turn instruction generation in natural language
- Personalized crowd rerouting suggestions

### Supporting Infrastructure (works without LLM, enables the GenAI layer)
- Dijkstra/A* pathfinding algorithm
- EWMA density trend calculation
- Threshold-based alert triggers
- JWT authentication + RBAC
- WebSocket/SSE real-time transport
- SVG map rendering
- Web Speech API voice I/O
