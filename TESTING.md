# SentinelArena — Testing Strategy

> Testing pyramid with measurable coverage targets and AI-specific evaluation.

## Testing Pyramid

```
         ╱╲
        ╱ E2E ╲           Playwright (3 critical journeys)
       ╱────────╲
      ╱ AI Eval  ╲        30 golden tests/agent (grounding, injection, latency)
     ╱────────────╲
    ╱ Integration   ╲     Testcontainers (Postgres, Redis)
   ╱──────────────────╲
  ╱    Unit Tests       ╲  Vitest (TS) + Pytest (Python) — ≥85% coverage
 ╱────────────────────────╲
╱   Static Analysis         ╲ ESLint, mypy, Ruff, TypeScript strict
╱────────────────────────────╲
```

## Layer Details

### 1. Static Analysis (Foundation)
- **TypeScript:** `strict: true`, `noImplicitAny`, `strictNullChecks`, `noUncheckedIndexedAccess`
- **Python:** `mypy --strict`, `ruff check`, `ruff format`
- **ESLint:** airbnb-typescript config
- **Prettier:** consistent formatting
- **Runs:** pre-commit hooks + CI

### 2. Unit Tests — Target: ≥85% line coverage on business logic
**Tools:** Vitest (TypeScript), Pytest (Python)

**Coverage scope (what counts):**
- Pathfinding algorithm (Dijkstra/A* with accessibility constraints)
- Density evaluator (EWMA calculation, threshold logic)
- Auth middleware (JWT validation, RBAC checks)
- Input validators (Pydantic/Zod schemas)
- Agent tool implementations
- UI component rendering + interaction

**Coverage exclusions (documented in config):**
- Generated code (Alembic migrations, OpenAPI specs)
- Configuration files
- Type definitions / interfaces
- Test files themselves

### 3. Integration Tests
**Tools:** Pytest + Testcontainers

- Real PostgreSQL container for database interaction tests
- Real Redis container for cache/pub-sub tests
- Agent orchestrator with mock LLM but real DB/cache
- API endpoint tests with real middleware stack

### 4. Contract Tests
**Approach:** JSON Schema validation

- Frontend Zod schemas validated against API response schemas
- Ensures frontend/backend type contracts stay in sync
- Breaks CI on schema mismatch

### 5. End-to-End Tests — 3 Critical Journeys
**Tools:** Playwright

| Journey | Description | Validates |
|---------|-------------|-----------|
| Fan Navigation | Fan asks for accessible route → receives map + instructions | Navigation Agent, pathfinding, i18n |
| Organizer Advisory | Dashboard shows crowd advisory → organizer approves broadcast | Crowd Agent, decision flow, audit log |
| Volunteer Incident | Volunteer files incident in Hindi → correctly triaged | Language Agent, incident workflow, i18n |

### 6. AI Evaluation Suite — 30 golden tests per agent
**Location:** `eval/`

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| **Grounding** | Cited-source regex + judge LLM faithfulness score (1-5) | Average ≥ 4/5 |
| **Injection refusal** | Prompt-injection attempts in fake incident reports | 0% injection success rate |
| **Latency** | Wall-clock timing of agent responses | Navigation <1.5s p95, Chat <800ms first-token |
| **Multilingual** | Back-translate + semantic similarity | Similarity ≥ 0.85 |

### 7. Accessibility Tests
**Tools:** `@axe-core/playwright`

- Integrated into E2E test suite
- Scans every page visited during E2E journeys
- Fails build on critical WCAG 2.2 AA violations
- Results included in `ACCESSIBILITY.md`

### 8. Security Tests
- Gitleaks secret scanning in CI
- `npm audit` / `pip-audit` dependency vulnerability scanning
- Prompt-injection tests (part of AI eval suite)
- CORS/header verification tests

## Coverage Reporting

```bash
# Python coverage
pytest --cov=app --cov-report=html --cov-report=term-missing

# TypeScript coverage
pnpm test:coverage  # Vitest with c8/istanbul

# Combined report
# Coverage badges generated in CI and displayed in README
```

## Future Work (Stretch Goals)

- **Mutation testing:** Stryker (TS) / mutmut (Python) on pathfinding and threshold logic
- **Chaos testing:** Inject failures in Redis/Postgres connections to verify graceful degradation
- **Performance regression testing:** Automated p95 latency checks in CI against baseline
