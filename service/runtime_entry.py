"""
AgentCore Runtime entrypoint for the GridWise F1 Fantasy Advisor.
Runs as a BedrockAgentCoreApp container separate from FastAPI.
"""
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


async def _run_advisor(payload: dict) -> str:
    """Execute the F1 advisor graph for one turn and return final text."""
    prompt = payload.get("prompt", "")
    user_jwt = payload.get("user_jwt")
    user_id = payload.get("user_id", "anonymous")
    session_id = payload.get("session_id")

    if not prompt:
        return "No prompt provided."

    try:
        from google.adk.runners import Runner  # type: ignore
        from google.genai import types as genai_types  # type: ignore
        from app.agent.agents import build_f1_advisor_graph

        advisor, session_service, memory_svc = build_f1_advisor_graph(
            user_jwt=user_jwt,
            user_id=user_id,
        )

        runner = Runner(
            agent=advisor,
            app_name="gridwise",
            session_service=session_service,
            memory_service=memory_svc,
        )

        # Get or create session
        session = await session_service.get_session(
            app_name="gridwise",
            user_id=user_id,
            session_id=session_id or user_id,
        )
        if session is None:
            session = await session_service.create_session(
                app_name="gridwise",
                user_id=user_id,
                session_id=session_id or user_id,
                state={"user_id": user_id},
            )

        content = genai_types.Content(
            role="user",
            parts=[genai_types.Part(text=prompt)],
        )

        final_text = ""
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id or user_id,
            new_message=content,
        ):
            if hasattr(event, "content") and event.content:
                for part in event.content.parts:
                    if hasattr(part, "text") and part.text:
                        final_text += part.text

        return final_text or "No response generated."

    except Exception as exc:
        logger.error("Runtime error: %s", exc, exc_info=True)
        return f"Error: {exc}"


def main():
    try:
        from bedrock_agentcore.runtime import BedrockAgentCoreApp  # type: ignore

        app = BedrockAgentCoreApp()

        @app.entrypoint
        async def handler(payload: dict) -> dict:
            result = await _run_advisor(payload)
            return {"response": result}

        logger.info("Starting GridWise AgentCore Runtime...")
        app.run()

    except ImportError:
        logger.error("bedrock_agentcore.runtime not available. Install bedrock-agentcore>=1.8.0")
        raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
