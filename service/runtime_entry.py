"""
AgentCore Runtime entrypoint for the GridWise F1 Fantasy Advisor.
Runs as a BedrockAgentCoreApp container separate from FastAPI.
"""
import json
import logging
import os
import uuid

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from google.adk.runners import Runner
from google.genai import types as genai_types

from app.agent.agents import build_f1_advisor_graph
from app.agent.memory import AgentCoreMemoryService, get_memory_service
from app.agent.session import AgentCoreSessionService, get_session_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

APP_NAME = "gridwise"

app = BedrockAgentCoreApp()

_session_service: AgentCoreSessionService = get_session_service()
_build_cache: dict = {"advisor": None, "memory_svc": None, "jwt": ""}


def _ensure_advisor(user_jwt: str | None):
    jwt_key = user_jwt or ""
    if _build_cache["advisor"] is not None and _build_cache["jwt"] == jwt_key:
        return _build_cache["advisor"], _build_cache["memory_svc"]

    advisor, _, memory_svc = build_f1_advisor_graph(user_jwt=user_jwt)
    _build_cache["advisor"] = advisor
    _build_cache["memory_svc"] = memory_svc
    _build_cache["jwt"] = jwt_key
    return advisor, memory_svc


async def _run_advisor(payload: dict) -> str:
    prompt = payload.get("prompt", "")
    user_jwt = payload.get("user_jwt")
    user_id = payload.get("user_id", "anonymous")
    session_id = payload.get("session_id") or str(uuid.uuid4())

    if not prompt:
        return "No prompt provided."

    advisor, memory_svc = _ensure_advisor(user_jwt)

    runner = Runner(
        agent=advisor,
        app_name=APP_NAME,
        session_service=_session_service,
        memory_service=memory_svc,
    )

    session = await _session_service.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if session is None:
        session = await _session_service.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id, state={"user_id": user_id}
        )

    content = genai_types.Content(role="user", parts=[genai_types.Part(text=prompt)])

    final_text = ""
    async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=content):
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    final_text += part.text

    return final_text or "No response generated."


@app.entrypoint
async def handler(payload: dict) -> str:
    try:
        result = await _run_advisor(payload)
        return json.dumps({"response": result})
    except Exception as exc:
        logger.error("Runtime error: %s", exc, exc_info=True)
        return json.dumps({"error": str(exc)})


if __name__ == "__main__":
    logger.info("Starting GridWise AgentCore Runtime...")
    app.run()
