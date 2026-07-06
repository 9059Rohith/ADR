"""SentinelArena — Chat Routes.

SSE streaming chat endpoint that routes user messages through the
agent orchestrator for real-time AI responses.
"""

from __future__ import annotations

import json
from typing import Any

import structlog
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = structlog.get_logger()
router = APIRouter()


class ChatRequest(BaseModel):
    """Chat message request."""

    message: str = Field(..., min_length=1, max_length=2000)
    locale: str = Field(default="en", pattern="^(en|hi|ta|te|es)$")
    user_location_id: str = Field(default="lobby-main")


class ChatResponse(BaseModel):
    """Chat response."""

    response: str
    intent: str
    locale: str
    sources: list[str] = []
    route_data: dict[str, Any] | None = None
    density_data: list[dict[str, Any]] | None = None


@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    body: ChatRequest,
) -> Any:
    """Process a chat message through the agent orchestrator.

    The message is classified by intent and routed to the appropriate
    specialized agent (Navigation, Crowd, Decision, or General).

    Args:
        request: FastAPI request (for accessing app state).
        body: Chat message with locale and user location.

    Returns:
        ChatResponse with AI-generated response and metadata.
    """
    orchestrator = request.app.state.orchestrator

    result = await orchestrator.process_message(
        message=body.message,
        locale=body.locale,
        user_location_id=body.user_location_id,
    )

    return ChatResponse(
        response=result.get("response", ""),
        intent=result.get("intent", "general"),
        locale=result.get("locale", body.locale),
        sources=result.get("sources", []),
        route_data=result.get("route_data"),
        density_data=result.get("density_data"),
    )


@router.post("/stream")
async def chat_stream(
    request: Request,
    body: ChatRequest,
) -> StreamingResponse:
    """Stream a chat response via Server-Sent Events (SSE).

    Provides first-token latency <800ms target by streaming
    response chunks as they're generated.

    Args:
        request: FastAPI request.
        body: Chat message.

    Returns:
        SSE stream of response chunks.
    """
    orchestrator = request.app.state.orchestrator

    async def event_generator():
        """Generate SSE events from the agent orchestrator."""
        try:
            result = await orchestrator.process_message(
                message=body.message,
                locale=body.locale,
                user_location_id=body.user_location_id,
            )

            # Send metadata first
            metadata = {
                "intent": result.get("intent", "general"),
                "sources": result.get("sources", []),
            }
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

            # Stream the response in chunks
            response_text = result.get("response", "")
            chunk_size = 50  # Characters per chunk
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i : i + chunk_size]
                yield f"data: {json.dumps({'text': chunk})}\n\n"

            # Send route data if available
            if result.get("route_data"):
                yield f"event: route\ndata: {json.dumps(result['route_data'])}\n\n"

            # Send done event
            yield "event: done\ndata: {}\n\n"

        except Exception as e:
            logger.error("Chat stream error", error=str(e))
            yield f"event: error\ndata: {json.dumps({'error': 'Internal server error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
