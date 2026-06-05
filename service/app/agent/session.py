"""
AgentCore Session service implementing Google ADK BaseSessionService.
Uses bedrock_agentcore.memory.MemoryClient for durable session event storage.
Session store ID is read from AGENTCORE_SESSION_MEMORY_ID env var or SSM.
"""
from __future__ import annotations

import asyncio
import logging
import os
import time
import uuid
from typing import Any, Optional

logger = logging.getLogger(__name__)

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
SESSION_MEMORY_ID_SSM = "/gridwise/agentcore/session-memory-id"

try:
    from google.adk.sessions.base_session_service import (  # type: ignore
        BaseSessionService,
        GetSessionConfig,
        ListSessionsResponse,
    )
    from google.adk.sessions.session import Session  # type: ignore
    from google.adk.events.event import Event  # type: ignore
    from google.adk.events.event_actions import EventActions  # type: ignore
    _ADK_AVAILABLE = True
except ImportError:
    _ADK_AVAILABLE = False
    BaseSessionService = object  # type: ignore
    GetSessionConfig = None  # type: ignore
    ListSessionsResponse = None  # type: ignore
    Session = None  # type: ignore
    Event = None  # type: ignore
    EventActions = None  # type: ignore

try:
    from bedrock_agentcore.memory import MemoryClient  # type: ignore
    _MEMORY_CLIENT_AVAILABLE = True
except ImportError:
    MemoryClient = None  # type: ignore
    _MEMORY_CLIENT_AVAILABLE = False


class AgentCoreSessionService(BaseSessionService):
    """ADK BaseSessionService backed by AWS AgentCore Memory.

    Each ADK Event is round-tripped through AgentCore as a single (text, role)
    message whose text is the JSON dump of the Event. Session state is rebuilt
    by replaying event.actions.state_delta on every get_session call.
    Falls back to in-memory only when MemoryClient is unavailable.
    """

    _ROLE_USER = "USER"
    _ROLE_ASSISTANT = "ASSISTANT"
    _ROLE_TOOL = "TOOL"
    _ROLE_OTHER = "OTHER"

    def __init__(self) -> None:
        if _ADK_AVAILABLE:
            super().__init__()
        self._memory_id: str = self._load_memory_id()
        self._client = None
        self._pending_sessions: dict[tuple[str, str, str], Any] = {}

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
        if self._client is None and self._memory_id and _MEMORY_CLIENT_AVAILABLE:
            try:
                self._client = MemoryClient(region_name=AWS_REGION)
            except Exception as exc:
                logger.warning("Could not create MemoryClient for sessions: %s", exc)
        return self._client

    @staticmethod
    def _encode_session_id(app_name: str, session_id: str) -> str:
        return f"{app_name}__{session_id}"

    @staticmethod
    def _decode_session_id(remote_session_id: str) -> tuple[Optional[str], str]:
        if "__" in remote_session_id:
            app_name, sid = remote_session_id.split("__", 1)
            return app_name, sid
        return None, remote_session_id

    @staticmethod
    def _role_for_event(event: Any) -> str:
        author = (getattr(event, "author", None) or "").lower()
        if author == "user":
            return AgentCoreSessionService._ROLE_USER
        try:
            if event.get_function_responses():
                return AgentCoreSessionService._ROLE_TOOL
        except Exception:
            pass
        if author:
            return AgentCoreSessionService._ROLE_ASSISTANT
        return AgentCoreSessionService._ROLE_OTHER

    @staticmethod
    def _serialize_event(event: Any) -> str:
        return event.model_dump_json(by_alias=True, exclude_none=True)

    def _events_for_session(self, *, app_name: str, user_id: str, session_id: str) -> list:
        remote_sid = self._encode_session_id(app_name, session_id)
        client = self._get_client()
        if not client or not self._memory_id:
            return []
        try:
            raw_events = client.list_events(
                memory_id=self._memory_id,
                actor_id=user_id,
                session_id=remote_sid,
                max_results=1000,
                include_payload=True,
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "validation" in msg or "not found" in msg or "no events" in msg:
                return []
            raise

        events = []
        for raw_event in (raw_events or []):
            for payload_item in raw_event.get("payload", []):
                conv = payload_item.get("conversational")
                if not conv:
                    continue
                text = (conv.get("content") or {}).get("text") or ""
                if text and Event is not None:
                    try:
                        events.append(Event.model_validate_json(text))
                    except Exception:
                        pass
        return events

    def _build_session_from_events(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        events: list,
        config: Any = None,
    ) -> Any:
        session = Session(
            id=session_id,
            app_name=app_name,
            user_id=user_id,
            events=[],
            state={},
            last_update_time=0.0,
        )
        for event in events:
            actions = getattr(event, "actions", None)
            if actions and getattr(actions, "state_delta", None):
                session.state.update(actions.state_delta)
            session.events.append(event)
            ts = getattr(event, "timestamp", None)
            if ts and ts > session.last_update_time:
                session.last_update_time = ts

        if config is not None:
            after_ts = getattr(config, "after_timestamp", None)
            if after_ts is not None:
                cutoff_index = 0
                for i in range(len(session.events) - 1, -1, -1):
                    if session.events[i].timestamp < after_ts:
                        cutoff_index = i + 1
                        break
                session.events = session.events[cutoff_index:]
            num_recent = getattr(config, "num_recent_events", None)
            if num_recent is not None:
                if num_recent <= 0:
                    session.events = []
                else:
                    session.events = session.events[-num_recent:]
        return session

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Any:
        sid = session_id or str(uuid.uuid4())
        session = Session(
            id=sid,
            app_name=app_name,
            user_id=user_id,
            state=dict(state) if state else {},
            events=[],
            last_update_time=time.time(),
        )
        remote_sid = self._encode_session_id(app_name, sid)
        client = self._get_client()
        if client and self._memory_id and session.state and Event is not None and EventActions is not None:
            init_event = Event(
                invocation_id="adk_session_init",
                author="system",
                actions=EventActions(state_delta=dict(session.state)),
            )
            try:
                await asyncio.to_thread(
                    client.create_event,
                    memory_id=self._memory_id,
                    actor_id=user_id,
                    session_id=remote_sid,
                    messages=[(self._serialize_event(init_event), self._ROLE_OTHER)],
                )
            except Exception as exc:
                logger.debug("Could not write init event: %s", exc)

        self._pending_sessions[(app_name, user_id, sid)] = session
        return session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Any = None,
    ) -> Optional[Any]:
        events = await asyncio.to_thread(
            self._events_for_session,
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        if events:
            return self._build_session_from_events(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id,
                events=events,
                config=config,
            )
        cached = self._pending_sessions.get((app_name, user_id, session_id))
        if cached is not None:
            try:
                return cached.model_copy(deep=True)
            except Exception:
                return cached
        return None

    async def list_sessions(self, *, app_name: str, user_id: Optional[str] = None) -> Any:
        prefix = f"{app_name}__"
        sessions = [
            s for (an, uid, _), s in self._pending_sessions.items()
            if an == app_name and (user_id is None or uid == user_id)
        ]
        if ListSessionsResponse is not None:
            return ListSessionsResponse(sessions=sessions)
        return sessions

    async def delete_session(self, *, app_name: str, user_id: str, session_id: str) -> None:
        remote_sid = self._encode_session_id(app_name, session_id)
        client = self._get_client()

        if client and self._memory_id:
            def _delete_all() -> None:
                while True:
                    events = client.list_events(
                        memory_id=self._memory_id,
                        actor_id=user_id,
                        session_id=remote_sid,
                        max_results=100,
                        include_payload=False,
                    )
                    if not events:
                        break
                    for event in events:
                        client.gmdp_client.delete_event(
                            memoryId=self._memory_id,
                            actorId=user_id,
                            sessionId=remote_sid,
                            eventId=event["eventId"],
                        )

            try:
                await asyncio.to_thread(_delete_all)
            except Exception as exc:
                msg = str(exc).lower()
                if "validation" not in msg and "not found" not in msg:
                    logger.warning("delete_session failed: %s", exc)

        self._pending_sessions.pop((app_name, user_id, session_id), None)

    async def append_event(self, session: Any, event: Any) -> Any:
        event = await super().append_event(session, event)
        if getattr(event, "partial", False):
            return event

        client = self._get_client()
        if not client or not self._memory_id:
            return event

        remote_sid = self._encode_session_id(session.app_name, session.id)
        try:
            await asyncio.to_thread(
                client.create_event,
                memory_id=self._memory_id,
                actor_id=session.user_id,
                session_id=remote_sid,
                messages=[(self._serialize_event(event), self._role_for_event(event))],
            )
        except Exception as exc:
            logger.warning("append_event failed: %s", exc)

        self._pending_sessions.pop((session.app_name, session.user_id, session.id), None)
        ts = getattr(event, "timestamp", None)
        if ts:
            session.last_update_time = ts
        return event


def get_session_service() -> Optional[AgentCoreSessionService]:
    """Factory — returns AgentCoreSessionService instance."""
    return AgentCoreSessionService()
