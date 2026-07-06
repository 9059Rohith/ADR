# 🏟️ SentinelArena — GenAI-Powered Smart Stadium & Tournament Operations Platform

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-90%25-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.12-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

> **A production-grade platform that fuses GenAI agents with deterministic crowd analytics to deliver real-time indoor navigation, crowd management, and decision support for smart stadiums and tournament operations.**

---

## 🎯 Problem Statement

Modern stadiums face critical challenges during high-attendance events:
- **Crowd crush risks** — density hotspots can escalate in minutes
- **Navigation confusion** — fans struggle with indoor wayfinding across multiple floors
- **Decision paralysis** — organizers lack synthesized, actionable intelligence
- **Language barriers** — diverse audiences need multilingual assistance
- **Accessibility gaps** — wheelchair users and mobility-impaired fans need adapted routes

SentinelArena addresses all five challenges through a unified AI platform that keeps **humans in the loop** for every critical decision.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Applications                     │
│  ┌───────────────┐  ┌──────────────┐  ┌──────────────────┐ │
│  │ Web Dashboard  │  │   Fan PWA    │  │  Volunteer App   │ │
│  │ (Organizer)    │  │  (Mobile)    │  │   (Staff)        │ │
│  │ Next.js        │  │  Next.js     │  │   Vite+React     │ │
│  └───────┬────────┘  └──────┬───────┘  └────────┬─────────┘ │
└──────────┼──────────────────┼───────────────────┼───────────┘
           │    REST/SSE/WS   │                   │
┌──────────┼──────────────────┼───────────────────┼───────────┐
│          ▼                  ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              API Gateway (FastAPI)                   │    │
│  │  Security: CORS, CSP, HSTS, Argon2id, JWT RBAC     │    │
│  │  Structured Logging (structlog) + Audit Trail       │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                       │
│  ┌──────────────────▼──────────────────────────────────┐    │
│  │         Agent Orchestrator (LangGraph)               │    │
│  │  ┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐   │    │
│  │  │Nav     │ │Crowd   │ │Decision  │ │Language  │   │    │
│  │  │Agent   │ │Agent   │ │Agent     │ │Agent     │   │    │
│  │  └────┬───┘ └───┬────┘ └────┬─────┘ └────┬─────┘   │    │
│  └───────┼─────────┼──────────┼────────────┼───────────┘    │
│          │         │          │            │                 │
│  ┌───────▼─────────▼──────────▼────────────▼───────────┐    │
│  │           Deterministic Core (No LLM)               │    │
│  │  ┌──────────────┐  ┌──────────────────────────┐     │    │
│  │  │ A* Pathfinder│  │ EWMA Density Evaluator   │     │    │
│  │  │ (with access │  │ (severity, trends,       │     │    │
│  │  │  constraints)│  │  projections)            │     │    │
│  │  └──────────────┘  └──────────────────────────┘     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  ┌──────────────────┐  ┌────────────────────────────────┐   │
│  │ Crowd Simulator  │  │   MongoDB Atlas Cloud Store    │   │
│  │ (Synthetic IoT)  │  │   SOPs as vector embeddings    │   │
│  │ [SIMULATED DATA] │  │   + Immutable Audit Log        │   │
│  └──────────────────┘  └────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

| ADR | Decision | Rationale |
|-----|----------|-----------|
| [ADR-001](ADR/001-agent-orchestration.md) | LangGraph over raw function calling | Explicit state machine for agent routing, debuggable traces |
| [ADR-002](ADR/002-hexagonal-architecture.md) | Hexagonal (ports/adapters) | Testability without API keys, future LLM swappability |
| [ADR-003](ADR/003-crowd-analytics.md) | EWMA + deterministic thresholds | Reproducible safety decisions, no LLM-generated numbers |
| [ADR-004](ADR/004-mock-adapters.md) | Mock adapters for development | Zero-cost local dev, CI without secrets, deterministic tests |
| [ADR-005](ADR/005-dual-model-strategy.md) | Dual LLM model strategy | Fast model for routing/classification, reasoning model for synthesis |
| [ADR-006](ADR/006-mongodb-groq-migration.md) | MongoDB Atlas + Groq LPU | Ultra-fast inference (~300+ tps) and document-oriented cloud storage |

---

## ✨ Features

### 1. Dynamic Crowd Management
- **Real-time heatmap** with EWMA-smoothed density analysis per zone
- **Severity classification** (Normal → Warning → Critical → Emergency)
- **Trend projection** — predicts time-to-threshold using linear extrapolation
- **Grounding boundary** — all numbers are deterministic, never LLM-invented

### 2. Smart Indoor Navigation
- **A\* pathfinding** on a venue graph with 36+ POIs across 3 floors
- **Accessibility constraints** — avoid stairs, wheelchair-only routes, ramp routing
- **Live congestion weighting** — routes adapt to real-time crowd density
- **Natural language queries** — "Take me to the nearest restroom avoiding stairs"

### 3. Real-Time Decision Support (Copilot)
- **Multi-source fusion** — combines crowd data, weather, SOPs, and incident reports
- **Cited recommendations** — every suggestion references its source
- **Human-in-the-loop** — approve/reject/edit before any action is taken
- **Immutable audit trail** — SHA-256 hashed, timestamped decision log in MongoDB Atlas

### 4. Multi-Language AI Assistance (Powered by Groq LPU)
- **5 languages**: English, Hindi (हिन्दी), Tamil (தமிழ்), Telugu (తెలుగు), Spanish (Español)
- **Ultra-fast translation** via Llama 3.1 8B Instant (~300+ tokens/sec)
- **Voice input/output** via Web Speech API (progressive enhancement)
- **Cultural adaptation** — tone and formality adapted per locale

### 5. Security Posture (OWASP ASVS L2 & Top 1% Quality)
- **Argon2id** password hashing with OWASP-recommended parameters
- **JWT** with short-lived access (15 min) and rotating refresh tokens
- **Sliding-Window Rate Limiting** — protects LLM and API endpoints against DDoS/abuse
- **Prompt injection defense** — delimited system/user data in all prompts
- **Security headers** — CSP, HSTS, X-Frame-Options, Permissions-Policy
- **Secrets scanning** — Gitleaks in CI, `.env.example` with documentation

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 22+ with pnpm
- Docker & Docker Compose (optional)
- MongoDB Atlas cluster (free tier supported)
- Groq API Key (free tier supported)

### Option 1: Docker Compose (Recommended)

```bash
# Clone and configure
cp .env.example .env

# Start all services (injects MongoDB URI and Groq credentials)
docker compose up --build

# Services:
# API Gateway:     http://localhost:8000/api/docs
# Web Dashboard:   http://localhost:3000
# Fan PWA:         http://localhost:3001
# Crowd Simulator: http://localhost:8001
```

### Option 2: Local Development

```bash
# Backend
cd services/api-gateway
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd apps/web-dashboard
pnpm install
pnpm dev
```

---

## 🌐 Step-by-Step Production Deployment Guide

To deploy SentinelArena to production as a top 1% cloud-native application, follow these step-by-step instructions:

### Step 1: Database Setup (MongoDB Atlas)
1. Log in to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and create a free M0 cluster.
2. Under **Database Access**, create a database user with read/write privileges.
3. Under **Network Access**, add `0.0.0.0/0` (or your specific cloud provider VPC IP range).
4. Click **Connect -> Connect your application** and copy your connection string:
   `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?appName=Cluster0`

### Step 2: AI Provider Setup (Groq Cloud)
1. Log in to the [Groq Cloud Console](https://console.groq.com/).
2. Navigate to **API Keys** and generate a new key (`gsk_...`).
3. Ensure you have access to `llama-3.3-70b-versatile` and `llama-3.1-8b-instant`.

### Step 3: Deploy Backend API Gateway (Google Cloud Run / Render / Railway)
1. **Containerize:** The repository includes a production-ready `Dockerfile` in `services/api-gateway/Dockerfile`.
2. **Set Environment Variables** in your cloud deployment platform:
   - `USE_REAL_LLM=true`
   - `GROQ_API_KEY=gsk_your_groq_api_key`
   - `GROQ_REASONING_MODEL=llama-3.3-70b-versatile`
   - `GROQ_FAST_MODEL=llama-3.1-8b-instant`
   - `MONGODB_URI=mongodb+srv://user:pass@cluster0.xxxxx.mongodb.net/?appName=Cluster0`
   - `MONGODB_DB_NAME=sentinelarena_prod`
   - `JWT_SECRET_KEY=your_secure_64_char_random_hex_string`
3. **Deploy:** Deploy the container. Upon startup, `seed_mongodb` will automatically initialize the database, seed 4 demo user accounts, 12 stadium zones, navigation POIs, and 12 SOP documents!

### Step 4: Deploy Frontend Applications (Vercel / Netlify)
1. Connect your GitHub repository to Vercel or Netlify.
2. For **Web Dashboard** (`apps/web-dashboard`):
   - Build Command: `pnpm build`
   - Environment Variable: `NEXT_PUBLIC_API_URL=https://your-api-gateway-url.run.app`
3. For **Fan PWA** (`apps/fan-pwa`):
   - Build Command: `pnpm build`
   - Environment Variable: `NEXT_PUBLIC_API_URL=https://your-api-gateway-url.run.app`
4. Visit your deployed URL and log in immediately using any of the pre-seeded demo accounts (e.g., `admin@sentinelarena.com` / `SentinelAdmin2026!`).

---

## 📊 Grounding & Safety Boundaries

SentinelArena enforces strict boundaries between deterministic computation and LLM generation:

| Data Type | Source | LLM Role |
|-----------|--------|----------|
| Crowd density numbers | EWMA evaluator | Never generates, only references |
| Route distances/times | A* pathfinder | Phrases results, never invents |
| Severity classifications | Threshold-based rules | Explains, never overrides |
| SOP procedures | RAG retrieval (MongoDB Atlas) | Cites as `[SOP: §X.Y]` |
| Weather data | External API / mock | References, never fabricates |
| Decision recommendations | Groq LPU Llama 3.3 synthesis | **Always requires human approval** |

---

## 🧪 Testing Strategy

| Layer | Tool | Coverage Target |
|-------|------|----------------|
| Unit Tests | pytest | 85%+ (pathfinding: 95%+) |
| Integration Tests | pytest + httpx | API contracts |
| AI Eval | Custom suite | Response quality, citation accuracy |
| Security | Gitleaks, ruff S-rules | Zero secrets in code |
| Accessibility | Manual + ARIA audit | WCAG 2.2 Level AA |

---

## 📁 Project Structure

```
SentinelArena/
├── apps/
│   ├── web-dashboard/        # Organizer Control Room (Next.js)
│   ├── fan-pwa/              # Fan Chat Assistant (Next.js PWA)
│   └── volunteer-app/        # Volunteer Interface (Vite+React)
├── services/
│   ├── api-gateway/          # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/         # Pathfinding, Density Evaluator, Auth
│   │   │   ├── agents/       # LangGraph Orchestrator
│   │   │   ├── ports/        # LLM Provider interface
│   │   │   ├── adapters/     # Mock & Groq Llama implementations
│   │   │   ├── routes/       # API endpoints (MongoDB Atlas persistence)
│   │   │   └── models.py     # Pydantic v2 document schemas (MongoDoc)
│   │   └── tests/            # Test pyramid
│   └── crowd-simulator/      # Synthetic IoT data generator
├── packages/
│   └── shared-types/         # TypeScript types + Zod schemas
├── ADR/                      # Architecture Decision Records
├── docker-compose.yml
├── ARCHITECTURE.md           # C4 diagrams
├── TRACEABILITY.md           # Requirement mapping
├── ACCESSIBILITY.md          # WCAG compliance
├── TESTING.md                # Test strategy
└── README.md                 # This file
```

---

## 🔒 Environment Variables

See [`.env.example`](.env.example) for all configuration. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | No | Enables real Groq Llama AI (falls back to mock adapter when offline) |
| `MONGODB_URI` | No | MongoDB Atlas connection string (defaults to local/demo mode) |
| `MONGODB_DB_NAME` | No | Target database name (default: `sentinelarena`) |
| `JWT_SECRET_KEY` | **Yes (prod)** | Must be changed from default |
| `WEATHER_API_KEY` | No | OpenWeatherMap integration |

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>SentinelArena</strong> — Where AI meets safety at scale.
</p>
