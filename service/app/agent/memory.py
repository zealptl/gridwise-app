"""
AgentCore Memory adapter.
Wraps AWS AgentCore long-term and short-term memory APIs.
Memory store ID is read from SSM parameter /gridwise/agentcore/memory-store-id.
"""
import os
import logging
import json
from typing import Any, Optional

logger = logging.getLogger(__name__)

MEMORY_STORE_SSM = "/gridwise/agentcore/memory-store-id"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class AgentCoreMemory:
    """Adapter between Google ADK session events and AWS AgentCore Memory.

    Implements both **short-term** (session-scoped, TTL-backed) and
    **long-term** (user-scoped, preference / history) memory operations.

    All public methods degrade gracefully: when AWS credentials are absent or
    the AgentCore SDK is unavailable, operations fall back to an in-process
    dict and log a warning instead of raising.
    """

    # Class-level in-process fallback cache used when AgentCore is unavailable.
    # Key format: ``"{session_id}:{key}"``
    _fallback_cache: dict[str, Any] = {}

    def __init__(self) -> None:
        self.memory_store_id: str = self._load_memory_store_id()
        self._client = None  # lazy boto3 client

    # ------------------------------------------------------------------
    # Configuration loading
    # ------------------------------------------------------------------

    def _load_memory_store_id(self) -> str:
        """Return the AgentCore Memory Store ID.

        Resolution order:
        1. ``AGENTCORE_MEMORY_STORE_ID`` environment variable.
        2. SSM Parameter Store (``/gridwise/agentcore/memory-store-id``).
        3. Empty string if both sources fail.
        """
        if store_id := os.getenv("AGENTCORE_MEMORY_STORE_ID"):
            logger.debug("AgentCore Memory Store ID loaded from environment variable.")
            return store_id

        try:
            import boto3

            ssm = boto3.client("ssm", region_name=AWS_REGION)
            resp = ssm.get_parameter(Name=MEMORY_STORE_SSM)
            store_id = resp["Parameter"]["Value"]
            logger.info("AgentCore Memory Store ID loaded from SSM: %s", store_id)
            return store_id
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not load AgentCore Memory Store ID from SSM (%s). "
                "Set AGENTCORE_MEMORY_STORE_ID env var for local dev.",
                exc,
            )
            return ""

    # ------------------------------------------------------------------
    # Internal client helper
    # ------------------------------------------------------------------

    def _get_client(self):
        """Return a lazily-initialised boto3 ``bedrock-agentcore`` client."""
        if not self._client:
            try:
                import boto3

                self._client = boto3.client("bedrock-agentcore", region_name=AWS_REGION)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not create AgentCore client: %s", exc)
        return self._client

    # ------------------------------------------------------------------
    # Long-term memory — read
    # ------------------------------------------------------------------

    def search_memory(self, user_id: str, query: str) -> list[dict]:
        """Search the long-term memory store for memories relevant to *query*.

        Args:
            user_id: The GridWise user ID used to scope the search.
            query: Natural-language search query.

        Returns:
            List of memory entry dicts (may be empty on error or no results).
        """
        client = self._get_client()
        if client is None or not self.memory_store_id:
            logger.warning(
                "AgentCore Memory unavailable — returning empty results for user '%s'.",
                user_id,
            )
            return []

        try:
            resp = client.retrieve_memories(
                memoryStoreId=self.memory_store_id,
                query=query,
                filter={"userId": user_id},
            )
            entries: list[dict] = resp.get("memories", [])
            logger.debug(
                "search_memory: found %d entries for user '%s'.", len(entries), user_id
            )
            return entries
        except Exception as exc:  # noqa: BLE001
            logger.warning("search_memory failed for user '%s': %s", user_id, exc)
            return []

    # ------------------------------------------------------------------
    # Long-term memory — write (session post-processing)
    # ------------------------------------------------------------------

    def add_session_to_memory(
        self, session_id: str, user_id: str, events: list
    ) -> None:
        """Persist session events to long-term memory after a recommendation is accepted.

        Args:
            session_id: The ADK session identifier.
            user_id: The GridWise user ID.
            events: List of session event dicts produced by the ADK session.
        """
        client = self._get_client()
        if client is None or not self.memory_store_id:
            logger.warning(
                "AgentCore Memory unavailable — session '%s' not persisted.", session_id
            )
            return

        try:
            client.store_memory(
                memoryStoreId=self.memory_store_id,
                userId=user_id,
                sessionId=session_id,
                events=events,
            )
            logger.info(
                "Session '%s' persisted to long-term memory for user '%s'.",
                session_id,
                user_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "add_session_to_memory failed for session '%s': %s", session_id, exc
            )

    # ------------------------------------------------------------------
    # Long-term memory — write (recommendation accepted)
    # ------------------------------------------------------------------

    async def write_recommendation_accepted(
        self,
        user_id: str,
        picks: dict,
        chips_used: list[str],
        preferences: dict,
    ) -> None:
        """Store a finalised team selection in long-term memory.

        Called after :class:`SubmissionAgent` successfully calls ``submit_team``.
        The stored record captures the accepted picks, any chips used, and
        inferred user preferences so future sessions can personalise advice.

        Args:
            user_id: GridWise user ID.
            picks: Dict with keys ``drivers``, ``constructors``, ``drs_boost``.
            chips_used: List of chip names activated in this game week.
            preferences: Inferred preference dict (e.g. risk appetite, driver
                focus) derived from the FantasyContextAgent / IntelAgent output.
        """
        client = self._get_client()
        if client is None or not self.memory_store_id:
            logger.warning(
                "AgentCore Memory unavailable — recommendation for user '%s' not persisted.",
                user_id,
            )
            return

        payload = {
            "type": "recommendation_accepted",
            "picks": picks,
            "chips_used": chips_used,
            "preferences": preferences,
        }

        try:
            client.store_memory(
                memoryStoreId=self.memory_store_id,
                userId=user_id,
                content=json.dumps(payload),
                memoryType="LONG_TERM",
            )
            logger.info(
                "Recommendation accepted event stored in long-term memory for user '%s'.",
                user_id,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "write_recommendation_accepted failed for user '%s': %s", user_id, exc
            )

    # ------------------------------------------------------------------
    # Short-term memory — write
    # ------------------------------------------------------------------

    async def write_session_context(
        self,
        session_id: str,
        key: str,
        data: Any,
        ttl_seconds: int = 3600,
    ) -> None:
        """Store a sub-agent result in short-term (session-scoped) memory.

        Sub-agents write their outputs here (e.g. key ``"f1_data"``,
        ``"intel"``, ``"fantasy_context"``) so that the orchestrator and
        downstream agents can retrieve them without re-running expensive calls.

        Falls back to an in-process dict when AgentCore is unavailable.

        Args:
            session_id: ADK session identifier.
            key: Logical label for the stored data (e.g. ``"f1_data"``).
            data: Serialisable data to store.
            ttl_seconds: How long (in seconds) the entry should live.
                Defaults to 1 hour.
        """
        cache_key = f"{session_id}:{key}"
        client = self._get_client()

        if client is None or not self.memory_store_id:
            logger.debug(
                "write_session_context: using in-process cache for key '%s'.", cache_key
            )
            AgentCoreMemory._fallback_cache[cache_key] = data
            return

        try:
            client.store_memory(
                memoryStoreId=self.memory_store_id,
                sessionId=session_id,
                key=key,
                content=json.dumps(data),
                memoryType="SHORT_TERM",
                ttlSeconds=ttl_seconds,
            )
            logger.debug(
                "write_session_context: stored key '%s' in AgentCore (ttl=%ds).",
                cache_key,
                ttl_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "write_session_context failed for key '%s', falling back to in-process cache: %s",
                cache_key,
                exc,
            )
            AgentCoreMemory._fallback_cache[cache_key] = data

    # ------------------------------------------------------------------
    # Short-term memory — read
    # ------------------------------------------------------------------

    async def read_session_context(
        self, session_id: str, key: str
    ) -> Optional[Any]:
        """Retrieve a previously stored sub-agent result.

        Args:
            session_id: ADK session identifier.
            key: Logical label used when writing the data.

        Returns:
            The stored data, or ``None`` if not found.
        """
        cache_key = f"{session_id}:{key}"
        client = self._get_client()

        if client is None or not self.memory_store_id:
            result = AgentCoreMemory._fallback_cache.get(cache_key)
            logger.debug(
                "read_session_context: in-process cache %s for key '%s'.",
                "hit" if result is not None else "miss",
                cache_key,
            )
            return result

        try:
            resp = client.retrieve_memory(
                memoryStoreId=self.memory_store_id,
                sessionId=session_id,
                key=key,
            )
            content = resp.get("content")
            if content is None:
                return None
            return json.loads(content)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "read_session_context failed for key '%s', falling back to in-process cache: %s",
                cache_key,
                exc,
            )
            return AgentCoreMemory._fallback_cache.get(cache_key)
