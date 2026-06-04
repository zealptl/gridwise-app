"""
Agent router — session creation and CopilotKit AG-UI streaming chat.
"""
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

_bearer = HTTPBearer()


async def get_raw_jwt(credentials: HTTPAuthorizationCredentials = Security(_bearer)) -> str:
    return credentials.credentials


# ---------------------------------------------------------------------------
# Session creation
# ---------------------------------------------------------------------------

class SessionResponse(BaseModel):
    session_id: str


@router.post("/sessions", response_model=SessionResponse)
async def create_session(user_id: str = Depends(get_current_user)) -> SessionResponse:
    """Creates a session ID for the advisor. Validates Cognito JWT."""
    try:
        from app.agent.agents import build_f1_advisor_graph  # noqa: F401
        session_id = str(uuid.uuid4())
        logger.info("Created session %s for user %s", session_id, user_id)
        return SessionResponse(session_id=session_id)
    except Exception as exc:
        logger.error("Failed to create session: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to create agent session") from exc


# ---------------------------------------------------------------------------
# CopilotKit AG-UI streaming chat
# CopilotKit v1.x POSTs this request body to runtimeUrl.
# ---------------------------------------------------------------------------

class CopilotKitMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    role: str
    content: Any = ""


class CopilotKitChatRequest(BaseModel):
    threadId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    runId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[CopilotKitMessage] = []
    # Fields CopilotKit sends that we don't need to act on
    actions: list[dict] = []
    agentSession: Optional[dict] = None
    agentStates: list[dict] = []
    extensions: dict = {}
    textEnabled: bool = True
    imageEnabled: bool = False


@router.post("/chat")
async def chat_stream(
    request: CopilotKitChatRequest,
    user_id: str = Depends(get_current_user),
    raw_jwt: str = Depends(get_raw_jwt),
) -> StreamingResponse:
    """AG-UI streaming endpoint consumed by CopilotKit's CopilotChat component."""
    return StreamingResponse(
        _stream_ag_ui(request, user_id, raw_jwt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# AG-UI event streaming
# ---------------------------------------------------------------------------

def _evt(payload: dict) -> str:
    return f"data: {json.dumps(payload)}\n\n"


async def _stream_ag_ui(
    request: CopilotKitChatRequest,
    user_id: str,
    user_jwt: str,
) -> AsyncGenerator[str, None]:
    thread_id = request.threadId
    run_id = request.runId
    msg_id = str(uuid.uuid4())

    # Extract the last user message
    user_message = ""
    for m in reversed(request.messages):
        if m.role == "user":
            user_message = m.content if isinstance(m.content, str) else ""
            break

    yield _evt({"type": "RUN_STARTED", "threadId": thread_id, "runId": run_id})

    if not user_message:
        yield _evt({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})
        return

    yield _evt({"type": "TEXT_MESSAGE_START", "messageId": msg_id, "role": "assistant"})

    try:
        from app.agent.agents import build_f1_advisor_graph
        from google.adk.runners import Runner  # type: ignore
        from google.adk.sessions import InMemorySessionService  # type: ignore
        from google.genai import types as genai_types  # type: ignore

        advisor = build_f1_advisor_graph(user_jwt=user_jwt)

        session_service = InMemorySessionService()
        session = await session_service.get_session(
            app_name="gridwise", user_id=user_id, session_id=thread_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name="gridwise",
                user_id=user_id,
                session_id=thread_id,
                state={"user_id": user_id},
            )

        runner = Runner(agent=advisor, app_name="gridwise", session_service=session_service)

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=user_message)],
        )

        async for event in runner.run_async(
            user_id=user_id,
            session_id=thread_id,
            new_message=content,
        ):
            ag_ui = _adk_event_to_ag_ui(event, msg_id, thread_id)
            for evt in ag_ui:
                yield evt

    except ImportError as exc:
        logger.error("ADK not installed: %s", exc)
        error_text = "Agent framework not available."
        yield _evt({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": error_text})
    except Exception as exc:
        logger.error("Agent stream error: %s", exc, exc_info=True)
        error_text = "An error occurred while processing your request."
        yield _evt({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": error_text})

    yield _evt({"type": "TEXT_MESSAGE_END", "messageId": msg_id})
    yield _evt({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})


def _adk_event_to_ag_ui(event: Any, msg_id: str, thread_id: str) -> list[str]:
    """Convert an ADK event to one or more AG-UI SSE data lines."""
    results: list[str] = []
    try:
        if not hasattr(event, "content") or not event.content:
            return results
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                results.append(_evt({
                    "type": "TEXT_MESSAGE_CONTENT",
                    "messageId": msg_id,
                    "delta": part.text,
                }))
            elif hasattr(part, "function_call") and part.function_call:
                fn = part.function_call
                tool_name = fn.name
                tool_input = dict(fn.args or {})
                # display_team_recommendation → STATE_SNAPSHOT for useCoAgentStateRender
                if tool_name == "display_team_recommendation":
                    results.append(_evt({
                        "type": "STATE_SNAPSHOT",
                        "snapshot": {tool_name: tool_input},
                        "threadId": thread_id,
                    }))
                else:
                    results.append(_evt({
                        "type": "TOOL_CALL",
                        "toolCallId": str(uuid.uuid4()),
                        "toolName": tool_name,
                        "toolInput": tool_input,
                    }))
    except Exception:
        pass
    return results
