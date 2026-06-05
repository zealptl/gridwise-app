"""
Agent router — session creation and CopilotKit AG-UI streaming chat.
"""
import json
import logging
import os
import uuid
import botocore.auth
import botocore.awsrequest
import botocore.session
import urllib.parse
import urllib.request
from typing import Any, AsyncGenerator, Optional

from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from app.agent import ADVISOR_AGENT_NAME
from app.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])

_bearer = HTTPBearer()

_SUB_AGENT_PROGRESS_KEYS: dict[str, str] = {
    "F1DataAgent": "f1DataAgent",
    "IntelAgent": "intelAgent",
    "FantasyContextAgent": "fantasyContextAgent",
}


async def get_raw_jwt(credentials: HTTPAuthorizationCredentials = Security(_bearer)) -> str:
    return credentials.credentials


def _extract_sub(jwt_token: str) -> Optional[str]:
    """Decode JWT without verification to extract sub claim."""
    try:
        from jose import jwt as jose_jwt
        claims = jose_jwt.get_unverified_claims(jwt_token)
        return claims.get("sub")
    except Exception:
        return None


def _get_runtime_endpoint() -> str:
    if url := os.getenv("AGENTCORE_RUNTIME_ENDPOINT"):
        return url
    try:
        import boto3
        ssm = boto3.client("ssm", region_name=os.getenv("AWS_REGION", "us-east-1"))
        return ssm.get_parameter(Name="/gridwise/agentcore/runtime-endpoint")["Parameter"]["Value"]
    except Exception:
        return ""


async def _invoke_runtime(endpoint: str, payload: dict) -> str:
    """Invoke AgentCore Runtime with SigV4-signed request."""
    import asyncio

    body = json.dumps(payload).encode()
    region = os.getenv("AWS_REGION", "us-east-1")

    def _sync_invoke():
        session = botocore.session.get_session()
        credentials = session.get_credentials().get_frozen_credentials()
        parsed = urllib.parse.urlparse(endpoint)

        request = botocore.awsrequest.AWSRequest(
            method="POST",
            url=endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Host": parsed.netloc},
        )
        signer = botocore.auth.SigV4Auth(credentials, "bedrock-agentcore", region)
        signer.add_auth(request)

        req = urllib.request.Request(endpoint, data=body, headers=dict(request.headers), method="POST")
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return result.get("response", "")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_invoke)


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
    # Validate sub claim can be extracted
    sub = _extract_sub(raw_jwt)
    if not sub:
        raise HTTPException(status_code=401, detail="Cannot extract user identity from token")

    return StreamingResponse(
        _stream_ag_ui(request, sub, raw_jwt),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
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
        runtime_endpoint = _get_runtime_endpoint()

        if runtime_endpoint:
            # Invoke AgentCore Runtime via SigV4
            response_text = await _invoke_runtime(runtime_endpoint, {
                "prompt": user_message,
                "user_jwt": user_jwt,
                "user_id": user_id,
                "session_id": thread_id,
            })
            if response_text:
                yield _evt({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": response_text})
        else:
            # Fallback: direct ADK runner (for local dev without AgentCore Runtime)
            from app.agent.agents import build_f1_advisor_graph
            from google.adk.runners import Runner  # type: ignore
            from google.genai import types as genai_types  # type: ignore

            result = build_f1_advisor_graph(user_jwt=user_jwt, user_id=user_id)
            if isinstance(result, tuple) and len(result) == 4:
                advisor, session_service, memory_svc, tools_available = result
            elif isinstance(result, tuple):
                advisor, session_service, memory_svc = result
                tools_available = True
            else:
                advisor = result
                from google.adk.sessions import InMemorySessionService  # type: ignore
                session_service = InMemorySessionService()
                memory_svc = None
                tools_available = True

            runner_kwargs = {"agent": advisor, "app_name": "gridwise", "session_service": session_service}
            if memory_svc:
                runner_kwargs["memory_service"] = memory_svc
            runner = Runner(**runner_kwargs)

            session = await session_service.get_session(app_name="gridwise", user_id=user_id, session_id=thread_id)
            if session is None:
                session = await session_service.create_session(app_name="gridwise", user_id=user_id, session_id=thread_id, state={"user_id": user_id})

            if not tools_available:
                sentinel = {
                    "f1_data":         {"available": False, "reason": "AgentCore tools unavailable"},
                    "intel":           {"available": False, "reason": "AgentCore tools unavailable"},
                    "fantasy_context": {"available": False, "reason": "AgentCore tools unavailable"},
                }
                session.state.update(sentinel)

            content = genai_types.Content(role="user", parts=[genai_types.Part(text=user_message)])

            async for event in runner.run_async(user_id=user_id, session_id=thread_id, new_message=content):
                author = getattr(event, "author", "")
                for ag_evt in _adk_event_to_ag_ui(event, msg_id, thread_id, author=author):
                    yield ag_evt

            yield _evt({
                "type": "STATE_SNAPSHOT",
                "snapshot": {"agentProgress": {v: "done" for v in _SUB_AGENT_PROGRESS_KEYS.values()}},
                "threadId": thread_id,
            })

    except HTTPException:
        raise
    except ImportError as exc:
        logger.error("ADK not installed: %s", exc)
        yield _evt({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": "Agent framework not available."})
    except Exception as exc:
        logger.error("Agent stream error: %s", exc, exc_info=True)
        yield _evt({"type": "TEXT_MESSAGE_CONTENT", "messageId": msg_id, "delta": "An error occurred while processing your request."})

    yield _evt({"type": "TEXT_MESSAGE_END", "messageId": msg_id})
    yield _evt({"type": "RUN_FINISHED", "threadId": thread_id, "runId": run_id})


def _adk_event_to_ag_ui(event: Any, msg_id: str, thread_id: str, author: str = "") -> list[str]:
    """Convert an ADK event to one or more AG-UI SSE data lines."""
    results: list[str] = []
    try:
        # Sub-agent events → emit progress snapshot, skip text content
        if author in _SUB_AGENT_PROGRESS_KEYS:
            progress_key = _SUB_AGENT_PROGRESS_KEYS[author]
            results.append(_evt({
                "type": "STATE_SNAPSHOT",
                "snapshot": {"agentProgress": {progress_key: "working"}},
                "threadId": thread_id,
            }))
            return results

        if not hasattr(event, "content") or not event.content:
            return results

        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                # Only emit text from the root advisor agent
                if author == ADVISOR_AGENT_NAME:
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
