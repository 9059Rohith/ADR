# SentinelArena — Architecture Document

> **Version:** 1.0 | **Last Updated:** 2025-01-15 | **Status:** Living Document

## 1. Context Diagram (C4 Level 1)

The system sits at the intersection of fans, volunteers, organizers, and external services:

```mermaid
C4Context
    title SentinelArena — System Context

    Person(fan, "Fan", "Spectator attending the tournament venue")
    Person(volunteer, "Volunteer / Staff", "On-ground operational personnel")
    Person(organizer, "Organizer", "Control room operator / event manager")

    System(sentinel, "SentinelArena", "AI-powered stadium operations platform providing crowd management, navigation, decision support, and multilingual assistance")

    System_Ext(groq, "Groq Cloud API (LPU Inference)", "Llama 3.3 70B & Llama 3.1 8B for reasoning, generation, and translation")
    System_Ext(weather, "Weather API", "Real-time weather data for venue area")
    System_Ext(iot, "IoT Sensors / Cameras", "Crowd density feeds [simulated in MVP]")

    Rel(fan, sentinel, "Uses", "HTTPS/WSS")
    Rel(volunteer, sentinel, "Uses", "HTTPS/WSS")
    Rel(organizer, sentinel, "Uses", "HTTPS/WSS")
    Rel(sentinel, groq, "Calls", "HTTPS")
    Rel(sentinel, weather, "Polls", "HTTPS")
    Rel(iot, sentinel, "Pushes data", "WebSocket/Redis Streams")
```

## 2. Container Diagram (C4 Level 2)

```mermaid
C4Container
    title SentinelArena — Container Diagram

    Person(fan, "Fan")
    Person(volunteer, "Volunteer")
    Person(organizer, "Organizer")

    Container_Boundary(frontend, "Frontend Applications") {
        Container(dashboard, "Web Dashboard", "Next.js, TypeScript", "Organizer control room: heatmaps, decision copilot, audit log")
        Container(pwa, "Fan PWA", "Next.js, TypeScript", "Mobile-first: chat, indoor map, voice navigation")
        Container(volapp, "Volunteer App", "React/Vite, TypeScript", "Task management, incident reporting, AI suggestions")
    }

    Container_Boundary(backend, "Backend Services") {
        Container(gateway, "API Gateway", "FastAPI, Python", "Auth, validation, rate limiting, routing, streaming")
        Container(orchestrator, "Agent Orchestrator", "LangGraph, Python", "Multi-agent AI: Crowd, Navigation, Decision, Language agents")
        Container(simulator, "Crowd Simulator", "FastAPI, Python", "Synthetic IoT data generation [documented mock]")
    }

    Container_Boundary(data, "Data Stores") {
        ContainerDb(mongodb, "MongoDB Atlas", "Cloud Database", "Users, venues, zones, POIs, SOPs, audit log, vector embeddings")
        ContainerDb(redis, "Redis", "Cache/PubSub", "Session cache, rate limits, pub/sub, semantic cache")
    }

    System_Ext(groq, "Groq Cloud API (LPU Inference)")
    System_Ext(weather, "Weather API")

    Rel(fan, pwa, "Uses")
    Rel(volunteer, volapp, "Uses")
    Rel(organizer, dashboard, "Uses")

    Rel(dashboard, gateway, "HTTPS/WSS")
    Rel(pwa, gateway, "HTTPS/WSS")
    Rel(volapp, gateway, "HTTPS/WSS")

    Rel(gateway, orchestrator, "Internal API")
    Rel(gateway, mongodb, "Async queries (Motor)")
    Rel(gateway, redis, "Cache/rate limit")

    Rel(orchestrator, groq, "LLM calls")
    Rel(orchestrator, mongodb, "RAG retrieval ($vectorSearch)")
    Rel(orchestrator, redis, "Pub/Sub, cache")

    Rel(simulator, redis, "Publishes density data")
    Rel(orchestrator, weather, "Weather queries")
```

## 3. Component Diagram — Agent Orchestrator (C4 Level 3)

```mermaid
flowchart TB
    subgraph Orchestrator ["Agent Orchestrator (LangGraph)"]
        Router["Router Node<br/>Intent Classification"]
        CrowdAgent["Crowd Agent<br/>Density Analysis + LLM Risk Assessment"]
        NavAgent["Navigation Agent<br/>NL → Pathfinding → NL Response"]
        DecisionAgent["Decision Agent<br/>Multi-source Fusion + Cited Recommendations"]
        LangAgent["Language Agent<br/>Locale-aware Translation + Tone"]
    end

    subgraph Tools ["Scoped Tools (Allow-listed)"]
        PathTool["Pathfinding Tool<br/>Dijkstra/A* on venue graph"]
        DensityTool["Density Query Tool<br/>Current + historical readings"]
        SOPTool["SOP Search Tool<br/>RAG over MongoDB Atlas"]
        WeatherTool["Weather Tool<br/>Current conditions"]
    end

    subgraph Ports ["Ports (Interfaces)"]
        LLMPort["LLM Provider Port"]
        VectorPort["Vector Store Port"]
        WeatherPort["Weather Provider Port"]
        CrowdPort["Crowd Data Source Port"]
    end

    subgraph Adapters ["Adapters (Implementations)"]
        GroqAdapter["Groq Llama Adapter"]
        MockLLM["Mock LLM Adapter"]
        AtlasVectorAdapter["MongoDB Atlas Vector Adapter"]
        MockWeather["Mock Weather Adapter"]
        RedisCrowd["Redis Crowd Source"]
    end

    Router --> CrowdAgent
    Router --> NavAgent
    Router --> DecisionAgent
    CrowdAgent --> LangAgent
    NavAgent --> LangAgent
    DecisionAgent --> LangAgent

    NavAgent --> PathTool
    CrowdAgent --> DensityTool
    DecisionAgent --> SOPTool
    DecisionAgent --> WeatherTool
    DecisionAgent --> DensityTool

    LLMPort -.-> GroqAdapter
    LLMPort -.-> MockLLM
    VectorPort -.-> AtlasVectorAdapter
    WeatherPort -.-> MockWeather
    CrowdPort -.-> RedisCrowd
```

## 4. Data Flow — Fan Navigation Query

```mermaid
sequenceDiagram
    participant Fan as Fan PWA
    participant GW as API Gateway
    participant Router as Router Node
    participant Nav as Navigation Agent
    participant Path as Pathfinding Tool
    participant LLM as Groq LPU API
    participant Lang as Language Agent

    Fan->>GW: POST /api/v1/chat {message, locale}
    GW->>GW: Validate JWT + rate limit
    GW->>Router: Classify intent (Llama 3.1 8B)
    Router->>Nav: navigation_intent detected
    Nav->>LLM: Extract constraints (Llama 3.3 70B)
    LLM-->>Nav: {destination: "Gate 3", constraints: ["no_stairs"]}
    Nav->>Path: find_route(from, to, constraints)
    Path-->>Nav: {route: [...nodes], distance: 240m, estimated_time: "3 min"}
    Nav->>LLM: Generate turn-by-turn instructions from route JSON
    LLM-->>Nav: "Head straight past Section B, take the elevator to Level 2..."
    Nav->>Lang: Translate to fan's locale
    Lang->>LLM: Translate to Hindi (Llama 3.1 8B)
    LLM-->>Lang: "सेक्शन B से सीधे जाएं, लेवल 2 तक लिफ्ट लें..."
    Lang-->>GW: SSE stream response
    GW-->>Fan: Streamed translated response + route overlay data
```

## 5. Security Architecture

```mermaid
flowchart LR
    subgraph External ["External Boundary"]
        Client["Client Apps"]
    end

    subgraph Gateway ["API Gateway"]
        CORS["CORS Filter"]
        Headers["Security Headers<br/>HSTS, CSP, X-Frame"]
        Auth["JWT Auth<br/>Short-lived access tokens"]
        RBAC["RBAC Middleware<br/>Role-based route guards"]
        Validate["Input Validation<br/>Pydantic v2 schemas"]
        RateLimit["Rate Limiter<br/>Sliding Window Algorithm"]
    end

    subgraph AI ["AI Layer"]
        PromptFence["Prompt Injection Defense<br/>Delimiter fencing"]
        ToolAllow["Tool Allow-listing<br/>4 scoped tools only"]
        OutputSanitize["Output Sanitization<br/>HTML/XSS filtering"]
        PIIRedact["PII Redaction<br/>Log sanitization"]
    end

    subgraph Data ["Data Layer"]
        Argon["Argon2id Hashing"]
        PydanticSchemas["Pydantic v2 Schemas<br/>Motor Async I/O"]
        AuditLog["Immutable Audit Log<br/>MongoDB Atlas"]
    end

    Client --> CORS --> Headers --> Auth --> RBAC --> Validate --> RateLimit
    RateLimit --> PromptFence --> ToolAllow --> OutputSanitize --> PIIRedact
    PIIRedact --> Argon
    PIIRedact --> PydanticSchemas
    PIIRedact --> AuditLog
```

## 6. Deployment Architecture

```mermaid
flowchart TB
    subgraph Docker ["Docker Compose Stack"]
        subgraph Services ["Application Services"]
        GW["API Gateway<br/>:8000"]
        Sim["Crowd Simulator<br/>:8001"]
        Dash["Web Dashboard<br/>:3000"]
        PWA["Fan PWA<br/>:3001"]
        Vol["Volunteer App<br/>:3002"]
    end

        subgraph Infra ["Local Cache"]
        RD["Redis 7<br/>:6379"]
    end
    end

    GW --> RD
    Sim --> RD

    subgraph External ["Cloud Services"]
        Mongo["MongoDB Atlas<br/>Cloud Cluster"]
        Groq["Groq Cloud API<br/>LPU Inference"]
        Weather["Weather API"]
    end

    GW --> Mongo
    GW --> Groq
    GW --> Weather
```

## 7. Key Design Decisions

See the [ADR/](./ADR/) folder for detailed Architecture Decision Records:

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [ADR-001](./ADR/001-langgraph-over-raw-function-calling.md) | LangGraph over raw function calling | Structured multi-agent orchestration with state management |
| [ADR-002](./ADR/002-postgres-pgvector-over-dedicated-vector-db.md) | Postgres+pgvector over dedicated vector DB | Single data store, simpler ops, sufficient for venue-scale data |
| [ADR-003](./ADR/003-fastapi-unified-gateway.md) | Unified FastAPI gateway | Consistent async Python stack, shared auth/middleware |
| [ADR-004](./ADR/004-mock-adapter-pattern.md) | Mock adapter pattern for external APIs | Clean testing, zero-config dev, swappable in production |
| [ADR-005](./ADR/005-dual-model-strategy.md) | Dual-model cost strategy | Fast model for routing, reasoning model for synthesis |
| [ADR-006](./ADR/006-mongodb-groq-migration.md) | MongoDB Atlas + Groq LPU | Ultra-fast inference (~300+ tps) and document-oriented cloud storage |
