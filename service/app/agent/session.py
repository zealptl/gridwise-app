"""
AgentCore Session service implementing Google ADK BaseSessionService.
Uses bedrock_agentcore.memory.MemoryClient for durable session event storage.
Session store ID is read from AGENTCORE_SESSION_MEMORY_ID env var or SSM.
"""
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SESSION_MEMORY_ID_SSM = "/gridwise/agentcore/session-memory-id"


class AgentCoreSessionService:
    """Google ADK BaseSessionService backed by AWS AgentCore session store Memory resource.

    Each ADK Event is JSON-serialized and stored via create_event.
    On get_session, events are reloaded via list_events and state is rebuilt by replaying state_deltas.
    Session IDs encoded as {app_name}__{session_id}.
    Partial events (event.partial=True) are not persisted.
    """

    def __init__(self) -> None:
        self.memory_id: str = self._load_memory_id()
        self._client = None
        self._pending_sessions: dict = {}

    def _load_memory_id(self) -> str:
        if mem_id := os.getenv("AGENTCORE_SESSION_MEMORY_ID"):
            return mem_id
        try:
            import boto3
            ssm = boto3.client("ssm", region_name=AWS_REGION)
            return ssm.get_parameter(Name=SESSION_MEMORY_ID_SSM)["Parameter"]["Value"]
        except Exception as exc:
            logger.warning("Could not load AGENTCORE_SESSION_MEMORY_ID from SSM: %s. Set env var for local dev.", exc)
            return ""

    def _get_client(self):
        if self._client is None and self.memory_id:
            try:
                from bedrock_agentcore.memory import MemoryClient  # type: ignore
                self._client = MemoryClient(region_name=AWS_REGION)
            except Exception as exc:
                logger.warning("Could not create MemoryClient for sessions: %s", exc)
        return self._client

    def _session_key(self, app_name: str, session_id: str) -> str:
        return f"{app_name}__{session_id}"

    async def create_session(self, app_name: str, user_id: str, state: Optional[dict] = None, session_id: Optional[str] = None):
        """Create a new session. Stores in _pending_sessions until first event is appended."""
        try:
            from google.adk.sessions.base_session_service import Session  # type: ignore
            import uuid
            sid = session_id or str(uuid.uuid4())
            session = Session(
                app_name=app_name,
                user_id=user_id,
                id=sid,
                state=state or {},
                events=[],
            )
            key = self._session_key(app_name, sid)
            self._pending_sessions[key] = session

            client = self._get_client()
            if client and self.memory_id and state:
                try:
                    client.create_event(
                        self.memory_id,
                        actor_id=user_id,
                        session_id=key,
                        messages=[{"role": "system", "content": f"init:{session_id}"}],
                    )
                except Exception as exc:
                    logger.debug("Could not write init event: %s", exc)

            return session
        except ImportError:
            return None

    async def get_session(self, app_name: str, user_id: str, session_id: str, config=None):
        """Retrieve session by replaying events from AgentCore or from _pending_sessions cache."""
        key = self._session_key(app_name, session_id)
        client = self._get_client()

        if client and self.memory_id:
            try:
                events_resp = client.list_events(
                    self.memory_id,
                    actor_id=user_id,
                    session_id=key,
                    include_payload=True,
                )
                raw_events = events_resp if isinstance(events_resp, list) else (events_resp or [])

                if raw_events:
                    try:
                        from google.adk.sessions.base_session_service import Session  # type: ignore
                        from google.adk.events import Event  # type: ignore

                        state: dict = {}
                        adk_events = []
                        for raw in raw_events:
                            payload = raw.get("payload") or raw.get("content")
                            if not payload:
                                continue
                            try:
                                evt = Event.model_validate_json(payload)
                                adk_events.append(evt)
                                if hasattr(evt, "actions") and evt.actions:
                                    delta = getattr(evt.actions, "state_delta", None)
                                    if delta:
                                        state.update(delta)
                            except Exception:
                                pass

                        return Session(
                            app_name=app_name,
                            user_id=user_id,
                            id=session_id,
                            state=state,
                            events=adk_events,
                        )
                    except Exception as exc:
                        logger.warning("Failed to deserialize session events: %s", exc)
            except Exception as exc:
                logger.warning("list_events failed for session %s: %s", key, exc)

        return self._pending_sessions.get(key)

    async def list_sessions(self, app_name: str, user_id: str):
        """List sessions for a user (returns pending sessions only for now)."""
        prefix = f"{app_name}__"
        sessions = [
            s for k, s in self._pending_sessions.items()
            if k.startswith(prefix) and s.user_id == user_id
        ]
        try:
            from google.adk.sessions.base_session_service import ListSessionsResponse  # type: ignore
            return ListSessionsResponse(sessions=sessions)
        except ImportError:
            return sessions

    async def delete_session(self, app_name: str, user_id: str, session_id: str) -> None:
        """Remove session from pending cache."""
        key = self._session_key(app_name, session_id)
        self._pending_sessions.pop(key, None)

    async def append_event(self, session, event) -> None:
        """Persist a single ADK event to the AgentCore session store."""
        if getattr(event, "partial", False):
            return

        client = self._get_client()
        if not client or not self.memory_id:
            return

        try:
            payload = event.model_dump_json(by_alias=True, exclude_none=True)
            key = self._session_key(session.app_name, session.id)
            client.create_event(
                self.memory_id,
                actor_id=session.user_id,
                session_id=key,
                messages=[{"role": "system", "content": payload}],
            )
        except Exception as exc:
            logger.warning("append_event failed: %s", exc)


def get_session_service() -> Optional[AgentCoreSessionService]:
    """Factory — returns AgentCoreSessionService instance."""
    return AgentCoreSessionService()
