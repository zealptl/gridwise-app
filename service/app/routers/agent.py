"""
AG-UI compatible agent router for the F1 Fantasy Advisor.
Exposes endpoints for session creation and streaming chat via CopilotKit.
"""
import json
import logging
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

_bearer = HTTPBearer()


async def get_raw_jwt(credentials: HTTPAuthorizationCredentials = Security(_bearer)) -> str:
    """Return the raw JWT string from the Authorization: Bearer header."""
    return credentials.credentials


# ---------------------------------------------------------------------------
# 9.2 — Session creation
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    session_id: str


@router.post("/sessions", response_model=SessionResponse)
async def create_session(user_id: str = Depends(get_current_user)) -> SessionResponse:
    """
    Creates a new ADK session and returns session_id.
    Requires valid Cognito JWT.
    """
    try:
        # Lazy import to avoid startup failures if ADK not installed
        from app.agent.agents import build_f1_advisor_graph  # noqa: F401 — verify importable

        # In production: create ADK Runner session here
        # For now: generate a session ID (Runner integration done in chat endpoint)
        session_id = str(uuid.uuid4())
        logger.info("Created session %s for user %s", session_id, user_id)
        return SessionResponse(session_id=session_id)
    except Exception as exc:
        logger.error("Failed to create session: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create agent session") from exc


# ---------------------------------------------------------------------------
# 9.3 — AG-UI streaming chat
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    session_id: str
    message: str
    context: dict = {}


@router.post("/chat")
async def chat_stream(
    request: ChatRequest,
    user_id: str = Depends(get_current_user),
    raw_jwt: str = Depends(get_raw_jwt),
) -> StreamingResponse:
    """
    Streaming AG-UI endpoint for CopilotKit.
    Runs the ADK Runner and streams AG-UI events back as Server-Sent Events.
    """
    return StreamingResponse(
        _stream_agent_response(request, user_id, raw_jwt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# 9.3 / 9.4 — Internal streaming helper
# ---------------------------------------------------------------------------

async def _stream_agent_response(
    request: ChatRequest,
    user_id: str,
    user_jwt: str,
) -> AsyncGenerator[str, None]:
    """
    Stream AG-UI events from the ADK Runner.

    Handles:
    - Session lookup / creation via InMemorySessionService
    - Runner construction and async event streaming
    - ADK-to-AG-UI event conversion
    - Structured error events so the client always receives a clean close
    """
    try:
        from app.agent.agents import build_f1_advisor_graph
        from google.adk.runners import Runner  # type: ignore
        from google.adk.sessions import InMemorySessionService  # type: ignore

        # Build the agent graph
        advisor = build_f1_advisor_graph(user_jwt=user_jwt)

        # Set up session service and inject user_id into session state
        session_service = InMemorySessionService()
        session = await session_service.get_session(
            app_name="gridwise",
            user_id=user_id,
            session_id=request.session_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name="gridwise",
                user_id=user_id,
                session_id=request.session_id,
                state={"user_id": user_id, **request.context},
            )

        # Create runner
        runner = Runner(
            agent=advisor,
            app_name="gridwise",
            session_service=session_service,
        )

        # Build the user content message
        from google.genai import types as genai_types  # type: ignore

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=request.message)],
        )

        # Stream response as AG-UI events
        async for event in runner.run_async(
            user_id=user_id,
            session_id=request.session_id,
            new_message=content,
        ):
            ag_ui_event = _convert_to_ag_ui_event(event)
            if ag_ui_event:
                yield f"data: {ag_ui_event}\n\n"

        # Signal stream end
        yield 'data: {"type":"done"}\n\n'

    except ImportError as exc:
        logger.error("ADK not installed: %s", exc)
        yield f'data: {json.dumps({"type": "error", "message": "Agent framework not available"})}\n\n'
    except Exception as exc:
        logger.error("Agent stream error: %s", exc, exc_info=True)
        yield f'data: {json.dumps({"type": "error", "message": "Agent error occurred"})}\n\n'


# ---------------------------------------------------------------------------
# 9.3 — ADK → AG-UI event conversion
# ---------------------------------------------------------------------------

def _convert_to_ag_ui_event(event) -> str | None:
    """Convert an ADK event to an AG-UI JSON string, or None to skip it."""
    try:
        # ADK events expose a .content attribute with the agent's response
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    return json.dumps({"type": "text_delta", "delta": part.text})
                if hasattr(part, "function_call") and part.function_call:
                    return json.dumps(
                        {
                            "type": "tool_call",
                            "tool_name": part.function_call.name,
                            "tool_input": dict(part.function_call.args or {}),
                        }
                    )
    except Exception:
        pass
    return None
