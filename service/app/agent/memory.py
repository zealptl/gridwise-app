"""
AgentCore Memory service implementing Google ADK BaseMemoryService.
Uses bedrock_agentcore.memory.MemoryClient for durable cross-session memory.
Memory ID is read from AGENTCORE_MEMORY_ID env var or SSM /gridwise/agentcore/memory-id.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
MEMORY_ID_SSM = "/gridwise/agentcore/memory-id"


class AgentCoreMemoryService:
    """Google ADK BaseMemoryService backed by AWS AgentCore long-term memory.

    Uses USER_PREFERENCE + SEMANTIC extraction strategies.
    actor_id is always the Cognito sub claim.
    """

    def __init__(self) -> None:
        self.memory_id: str = self._load_memory_id()
        self._client = None

    def _load_memory_id(self) -> str:
        if mem_id := os.getenv("AGENTCORE_MEMORY_ID"):
            return mem_id
        try:
            import boto3
            ssm = boto3.client("ssm", region_name=AWS_REGION)
            return ssm.get_parameter(Name=MEMORY_ID_SSM)["Parameter"]["Value"]
        except Exception as exc:
            logger.warning("Could not load AGENTCORE_MEMORY_ID from SSM: %s. Set env var for local dev.", exc)
            return ""

    def _get_client(self):
        if self._client is None and self.memory_id:
            try:
                from bedrock_agentcore.memory import MemoryClient  # type: ignore
                self._client = MemoryClient(region_name=AWS_REGION)
            except Exception as exc:
                logger.warning("Could not create MemoryClient: %s", exc)
        return self._client

    async def search_memory(self, app_name: str, user_id: str, query: str):
        """Search long-term memory for context relevant to query.

        Returns SearchMemoryResponse with combined MemoryEntry objects.
        actor_id = user_id (Cognito sub claim).
        """
        try:
            from google.adk.memory.base_memory_service import SearchMemoryResponse, MemoryEntry  # type: ignore
        except ImportError:
            return None

        client = self._get_client()
        if not client or not self.memory_id:
            logger.debug("AgentCore Memory unavailable — returning empty search results.")
            return SearchMemoryResponse(memories=[])

        memories = []
        try:
            turns = client.get_last_k_turns(
                self.memory_id,
                actor_id=user_id,
                session_id=app_name,
                k=5,
            )
            for turn in (turns or []):
                content = turn.get("content") or str(turn)
                memories.append(MemoryEntry(content=content, score=1.0))
        except Exception as exc:
            logger.warning("get_last_k_turns failed: %s", exc)

        try:
            results = client.retrieve_memories(
                self.memory_id,
                namespace=f"{user_id}/{app_name}",
                query=query,
                top_k=5,
            )
            for r in (results or []):
                content = r.get("content") or str(r)
                score = r.get("score", 0.5)
                memories.append(MemoryEntry(content=content, score=score))
        except Exception as exc:
            logger.warning("retrieve_memories failed: %s", exc)

        return SearchMemoryResponse(memories=memories)

    async def add_session_to_memory(self, session) -> None:
        """Persist completed session events to long-term memory for extraction.

        Collects text events and stores them via create_event.
        Skips if no text events found.
        actor_id = session.user_id (Cognito sub claim).
        """
        client = self._get_client()
        if not client or not self.memory_id:
            logger.debug("AgentCore Memory unavailable — session not persisted.")
            return

        try:
            events = getattr(session, "events", []) or []
            messages = []
            for event in events:
                if getattr(event, "partial", False):
                    continue
                content = getattr(event, "content", None)
                if not content:
                    continue
                parts = getattr(content, "parts", []) or []
                for part in parts:
                    text = getattr(part, "text", None)
                    if text:
                        role = getattr(content, "role", "assistant")
                        messages.append({"role": role, "content": text})

            if not messages:
                return

            client.create_event(
                self.memory_id,
                actor_id=session.user_id,
                session_id=session.id,
                messages=messages,
            )
            logger.info("Session %s persisted to long-term memory for user %s.", session.id, session.user_id)
        except Exception as exc:
            logger.warning("add_session_to_memory failed: %s", exc)


def get_memory_service() -> Optional[AgentCoreMemoryService]:
    """Factory — returns AgentCoreMemoryService instance."""
    return AgentCoreMemoryService()
