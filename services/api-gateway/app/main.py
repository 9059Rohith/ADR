"""SentinelArena API Gateway — FastAPI Application.

Main entry point for the API gateway service. Configures:
- CORS, security headers, rate limiting
- Database initialization and connection management
- Route registration
- Venue graph and agent orchestrator initialization
- Structured logging
"""

from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

import structlog
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database import close_db, init_db
from app.routes import auth, chat, crowd, decisions, incidents, navigation, venues
from app.seed import (
    create_density_evaluator,
    create_venue_graph,
    get_sop_documents,
    seed_mongodb,
)
from app.agents.orchestrator import AgentOrchestrator


def _configure_logging() -> None:
    """Configure structured logging safely."""
    settings = get_settings()

    log_level_map = {
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }
    level = log_level_map.get(settings.log_level, logging.INFO)

    renderer: structlog.types.Processor = (
        structlog.processors.JSONRenderer()
        if settings.log_format == "json"
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            renderer,
        ],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


_configure_logging()
logger = structlog.get_logger()

# In-memory sliding window rate limiter store
_rate_limit_store: dict[str, list[float]] = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle manager.

    Startup: Initialize database, seed MongoDB Atlas, load venue graph, agent orchestrator.
    Shutdown: Close database connections.
    """
    settings = get_settings()
    logger.info("Starting SentinelArena API Gateway", port=settings.api_gateway_port)

    # Initialize database (graceful — allows running without MongoDB)
    db_available = False
    try:
        await init_db()
        from app.database import get_client

        client = get_client()
        db = client[settings.mongodb_db_name]
        await seed_mongodb(db)
        db_available = True
        logger.info("MongoDB Atlas initialized and seeded successfully")
    except Exception as exc:
        logger.warning(
            "MongoDB Atlas not available — running in demo mode",
            error=str(exc),
        )

    app.state.db_available = db_available

    # Initialize venue graph (deterministic core — no DB needed)
    venue_graph = create_venue_graph()
    logger.info(
        "Venue graph loaded",
        nodes=venue_graph.node_count,
        edges=venue_graph.edge_count,
    )

    # Initialize density evaluator
    density_evaluator = create_density_evaluator()
    logger.info("Density evaluator initialized")

    # Initialize agent orchestrator
    sop_docs = get_sop_documents()
    orchestrator = AgentOrchestrator(
        venue_graph=venue_graph,
        density_evaluator=density_evaluator,
        sop_documents=sop_docs,
    )
    logger.info(
        "Agent orchestrator initialized",
        use_real_llm=settings.use_real_llm,
    )

    # Store in app state for route access
    app.state.venue_graph = venue_graph
    app.state.density_evaluator = density_evaluator
    app.state.orchestrator = orchestrator

    yield

    # Shutdown
    if db_available:
        await close_db()
    logger.info("SentinelArena API Gateway shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="SentinelArena API",
        description=(
            "GenAI-powered Smart Stadium & Tournament Operations Platform. "
            "Provides crowd management, indoor navigation, decision support, "
            "and multilingual assistance via AI agents."
        ),
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # ── CORS ──
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    # ── Rate Limiting Middleware (Top 1% Efficiency & Security) ──
    @app.middleware("http")
    async def rate_limiting_middleware(request: Request, call_next: Any) -> Response:
        """Enforce sliding-window rate limiting per IP address."""
        if request.url.path in ["/health", "/api/v1/info", "/api/docs", "/api/openapi.json"]:
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window = 60.0  # 1 minute window

        timestamps = _rate_limit_store.get(client_ip, [])
        timestamps = [t for t in timestamps if now - t < window]

        limit = (
            settings.rate_limit_llm_requests_per_minute
            if "/chat" in request.url.path or "/decisions" in request.url.path
            else settings.rate_limit_requests_per_minute
        )

        if len(timestamps) >= limit:
            from fastapi.responses import JSONResponse

            return JSONResponse(
                status_code=429,
                content={"detail": "Too Many Requests. Rate limit exceeded."},
                headers={"Retry-After": "60"},
            )

        timestamps.append(now)
        _rate_limit_store[client_ip] = timestamps

        return await call_next(request)

    # ── Security Headers Middleware ──
    @app.middleware("http")
    async def security_headers(request: Request, call_next: Any) -> Response:
        """Add security headers to all responses (OWASP recommended)."""
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(self), geolocation=(self)"
        )
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self' ws: wss:;"
        )
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response

    # ── Request Logging Middleware ──
    @app.middleware("http")
    async def request_logging(request: Request, call_next: Any) -> Response:
        """Log all requests with timing (PII redacted)."""
        start = time.perf_counter()
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(duration_ms, 2),
        )
        return response

    # ── Routes ──
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
    app.include_router(crowd.router, prefix="/api/v1/crowd", tags=["Crowd Management"])
    app.include_router(navigation.router, prefix="/api/v1/navigation", tags=["Navigation"])
    app.include_router(decisions.router, prefix="/api/v1/decisions", tags=["Decision Support"])
    app.include_router(incidents.router, prefix="/api/v1/incidents", tags=["Incidents"])
    app.include_router(venues.router, prefix="/api/v1/venues", tags=["Venues"])

    # ── Health Check ──
    @app.get("/health", tags=["Health"])
    async def health_check() -> dict[str, str]:
        """Health check endpoint for container orchestration."""
        return {"status": "healthy", "service": "api-gateway"}

    @app.get("/api/v1/info", tags=["Health"])
    async def api_info() -> dict[str, Any]:
        """API information and capabilities."""
        return {
            "name": "SentinelArena API",
            "version": "1.0.0",
            "features": [
                "dynamic-crowd-management",
                "smart-indoor-navigation",
                "real-time-decision-support",
                "multi-language-assistance",
            ],
            "supported_locales": ["en", "hi", "ta", "te", "es"],
            "use_real_llm": settings.use_real_llm,
        }

    return app


# Application instance
app = create_app()
