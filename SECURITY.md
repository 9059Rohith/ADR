# SentinelArena — Security Documentation

> **Standard:** OWASP ASVS Level 2 | **Last Reviewed:** 2026-07-08

## Security Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐                    │
│  │Dashboard │   │ Fan PWA  │   │Volunteer │ (all use HTTPS)     │
│  │ :3000    │   │ :3001    │   │App :3002 │                     │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘                    │
│       └──────────────┼──────────────┘                           │
│                      │ JWT Bearer Tokens                        │
│                      ▼                                          │
│  ┌──────────────────────────────────────────┐                   │
│  │           API Gateway (:8000)            │                   │
│  │  ┌────────────────────────────────────┐  │                   │
│  │  │ Security Middleware Stack          │  │                   │
│  │  │ ┌──────────────────────────────┐   │  │                   │
│  │  │ │ 1. Rate Limiter (100/min)    │   │  │                   │
│  │  │ │ 2. CORS Validation           │   │  │                   │
│  │  │ │ 3. Security Headers (CSP)    │   │  │                   │
│  │  │ │ 4. JWT Authentication        │   │  │                   │
│  │  │ │ 5. RBAC Authorization        │   │  │                   │
│  │  │ │ 6. Input Validation (Pydantic)│  │  │                   │
│  │  │ └──────────────────────────────┘   │  │                   │
│  │  └────────────────────────────────────┘  │                   │
│  └──────────────────────────────────────────┘                   │
│                      │                                          │
│  ┌──────────────────────────────────────────┐                   │
│  │          MongoDB Atlas (encrypted)       │                   │
│  │  • TLS/SSL connections                   │                   │
│  │  • IP whitelist                          │                   │
│  │  • Unique indexes on email               │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

## Authentication & Authorization

### Password Security
- **Algorithm:** Argon2id (winner of the Password Hashing Competition)
- **Implementation:** `argon2-cffi` library with recommended parameters
- **Properties:**
  - Memory-hard (resistant to GPU/ASIC attacks)
  - Side-channel resistant
  - Unique salt per password (automatic)

### JWT Token Management
- **Access tokens:** Short-lived (15 minutes default, configurable)
- **Refresh tokens:** Longer-lived (7 days default, configurable)
- **Token type enforcement:** Refresh tokens cannot be used as access tokens
- **Unique JTI:** Every token has a unique identifier for revocation support
- **Algorithm:** HS256 (configurable)

### Role-Based Access Control (RBAC)
```
Admin > Organizer > Volunteer > Fan
```
- Hierarchical role system
- Route-level protection via dependency injection
- All role checks tested in unit tests

## Input Validation

### Backend (Python)
- **Pydantic v2** with strict mode for all API request models
- Field-level constraints: `min_length`, `max_length`, `pattern` (regex)
- Email validation, password strength enforcement
- Severity enums with whitelist patterns: `^(low|medium|high|critical)$`

### Frontend (TypeScript)
- **Zod** schema validation on all form inputs
- `strict: true` TypeScript configuration with `noImplicitAny`
- HTML5 form validation as defense-in-depth

## HTTP Security Headers

Applied via `SecurityHeadersMiddleware` in `app/main.py`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `Content-Security-Policy` | `default-src 'self'; ...` | Prevent XSS/injection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer leaking |
| `Permissions-Policy` | `camera=(), microphone=(self)` | Restrict browser APIs |
| `Cache-Control` | `no-store` (on API responses) | Prevent sensitive data caching |

## Rate Limiting

- **Implementation:** IP-based rate limiting middleware
- **Default limit:** 100 requests per minute per IP
- **Response:** HTTP 429 with `Retry-After` header
- **Configurable:** Via environment variable `RATE_LIMIT_PER_MINUTE`

## CORS Configuration

- Explicit origin whitelist (no wildcards in production)
- Configurable via `ALLOWED_ORIGINS` environment variable
- `Access-Control-Allow-Credentials: true` only for whitelisted origins
- Default: `http://localhost:3000,3001,3002` (development only)

## LLM/AI Security

### Prompt Injection Defense
- **System prompt hardening:** Clear role boundaries in all agent system prompts
- **Input sanitization:** User messages are length-limited (2000 chars max)
- **Output grounding:** LLM responses are validated against deterministic data sources
- **Never trust LLM output for:** Route calculations, density numbers, authentication decisions

### Grounding Architecture
The LLM is used only for:
1. Natural language understanding (intent classification)
2. Response phrasing (translation/formatting)
3. RAG retrieval synthesis

All factual data comes from deterministic sources:
- **Pathfinding:** A* algorithm (deterministic)
- **Crowd density:** EWMA calculations (deterministic)
- **SOP references:** Exact document retrieval

## Dependency Security

### Automated Scanning
- **`pip-audit`:** Python dependency vulnerability scanning in CI
- **`pnpm audit`:** Node.js dependency vulnerability scanning in CI
- **Gitleaks:** Secret detection in CI pipeline
- **Dependabot:** Automated dependency update PRs (configured in `.github/dependabot.yml`)

### Supply Chain
- Pinned minimum versions in `requirements.txt`
- `pnpm-lock.yaml` for deterministic Node.js installs
- Multi-stage Docker builds (minimal attack surface in production images)

## Audit Trail

All decision actions (approve/reject/edit) are logged to an immutable audit trail:

```python
class AuditLog(BaseModel):
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    payload: dict
    payload_hash: str  # SHA-256 integrity hash
    created_at: datetime  # Server-side timestamp (UTC)
```

- **Immutable:** Insert-only collection in MongoDB Atlas
- **Integrity:** SHA-256 hash of payload for tamper detection
- **Indexed:** By actor, resource, and timestamp for efficient querying

## Environment Variable Security

- **Secret management:** All secrets via environment variables (never in code)
- **`.env.example`** provided with placeholder values
- **`.gitignore`** excludes `.env`, `*.pem`, `*.key` files
- **CI secrets:** Stored in GitHub Actions encrypted secrets

## Known Limitations & Mitigations

| Limitation | Mitigation | Priority |
|-----------|------------|----------|
| JWT tokens stored in localStorage | Short expiry (15min), refresh token rotation | Medium |
| No CSRF tokens on API | JWT Bearer auth (not cookie-based) eliminates CSRF | N/A |
| Rate limiting is in-memory | Acceptable for single-instance deployment; Redis-backed for scale | Low |
| No WAF in development | Recommended for production: Cloudflare or AWS WAF | Production |

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly to the SentinelArena team.
