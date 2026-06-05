## ADDED Requirements

### Requirement: Two AgentCore Memory CDK resources in the stack
The CDK stack SHALL define two `agentcore.Memory` resources:

1. **Session Store** (`GridwiseSessionMemory`) — no extraction strategies, used as a durable event log backing `AgentCoreSessionService`. Expiry: 30 days.
2. **Long-term Memory** (`GridwiseLongTermMemory`) — with `USER_PREFERENCE` and `SEMANTIC` built-in extraction strategies, used as `AgentCoreMemoryService`. Expiry: 90 days.

Both resource IDs SHALL be written to SSM as `CfnOutput` values and as SSM parameters so the FastAPI service can read them at startup without hardcoding.

SSM parameters written by CDK:
- `/gridwise/agentcore/session-memory-id` — ID of the session store memory resource
- `/gridwise/agentcore/memory-id` — ID of the long-term memory resource

#### Scenario: Session store created with no strategies
- **WHEN** `cdk deploy` completes
- **THEN** `GridwiseSessionMemory` exists in AWS with zero extraction strategies and 30-day expiry

#### Scenario: Long-term memory created with USER_PREFERENCE and SEMANTIC strategies
- **WHEN** `cdk deploy` completes
- **THEN** `GridwiseLongTermMemory` exists in AWS with both `USER_PREFERENCE` and `SEMANTIC` extraction strategies active and 90-day expiry

#### Scenario: Memory IDs written to SSM after deploy
- **WHEN** `cdk deploy` completes
- **THEN** `/gridwise/agentcore/session-memory-id` and `/gridwise/agentcore/memory-id` exist in SSM Parameter Store with the correct resource IDs

### Requirement: bedrock-agentcore Python package added to service dependencies
`service/pyproject.toml` SHALL declare `bedrock-agentcore >= 1.8.0` as a runtime dependency. The current `memory.py` uses `boto3.client("bedrock-agentcore")` which is incorrect — the real SDK is the `bedrock_agentcore` package.

#### Scenario: Package importable after install
- **WHEN** `uv sync` (or `pip install`) runs in the service directory
- **THEN** `from bedrock_agentcore.memory import MemoryClient` succeeds without ImportError

### Requirement: memory.py rewritten using MemoryClient and BaseMemoryService
`service/app/agent/memory.py` SHALL be completely rewritten. The current implementation uses fictional boto3 method names (`store_memory`, `retrieve_memories`, `retrieve_memory`) that do not exist. The replacement SHALL implement `google.adk.memory.base_memory_service.BaseMemoryService` using `bedrock_agentcore.memory.MemoryClient`.

The rewritten class SHALL be named `AgentCoreMemoryService` and implement:

- `search_memory(app_name, user_id, query)` → combines:
  - `client.get_last_k_turns(memory_id, actor_id=user_id, session_id=app_name, k=5)` for recent verbatim turns
  - `client.retrieve_memories(memory_id, namespace, query, top_k=5)` for each strategy namespace (USER_PREFERENCE, SEMANTIC)
  - Returns `SearchMemoryResponse` with all combined `MemoryEntry` objects

- `add_session_to_memory(session)` → calls `client.create_event(memory_id, actor_id=session.user_id, session_id=session.id, messages=[...])` with all text events from the session batched into one call

The `actor_id` SHALL always be the Cognito `sub` claim extracted from the user's JWT — never username or email.

Strategy namespaces SHALL follow the pattern:
- USER_PREFERENCE: read from `client.get_memory_strategies(memory_id)` at init (cached), substituting `{actorId}` with the user's `sub` claim
- SEMANTIC: same pattern

The `MemoryClient` SHALL be lazily initialized on first use, reading `AGENTCORE_MEMORY_ID` from environment or `/gridwise/agentcore/memory-id` from SSM as fallback.

#### Scenario: search_memory returns short-term and long-term results
- **WHEN** `search_memory(app_name="gridwise-advisor", user_id="<sub>", query="chip strategy")` is called
- **THEN** returns recent verbatim turns from `get_last_k_turns` combined with USER_PREFERENCE and SEMANTIC extractions matching the query

#### Scenario: add_session_to_memory batches all events in one create_event call
- **WHEN** a session with 4 user/assistant exchanges ends and `add_session_to_memory(session)` is called
- **THEN** one `client.create_event(...)` call is made with all (text, role) pairs in the `messages` list

#### Scenario: Empty session produces no create_event call
- **WHEN** `add_session_to_memory(session)` is called with a session containing no text events
- **THEN** no `client.create_event(...)` call is made

#### Scenario: actor_id is Cognito sub claim, not username
- **WHEN** memory is read or written for a user whose Cognito sub is `"a1b2-..."` and username is `"zeal"`
- **THEN** all MemoryClient calls use `actor_id="a1b2-..."`, never `"zeal"`

### Requirement: session.py created implementing AgentCoreSessionService
`service/app/agent/session.py` SHALL be a new file implementing `google.adk.sessions.base_session_service.BaseSessionService` backed by AgentCore Memory (the session store resource — no extraction strategies). This replaces `InMemorySessionService` so sessions survive FastAPI restarts and work across replicas.

The class SHALL implement all required methods:
- `create_session(app_name, user_id, state, session_id)` — mints a session; if seed state exists, writes an init event to AgentCore
- `get_session(app_name, user_id, session_id, config)` — rehydrates from AgentCore via `list_events`; replays `state_delta`s; falls back to in-process cache for sessions with no events yet
- `list_sessions(app_name, user_id)` — enumerates via AgentCore's session listing
- `delete_session(app_name, user_id, session_id)` — deletes all events for the session
- `append_event(session, event)` — calls `super().append_event()` then persists the trimmed event as JSON to AgentCore via `create_event`

Each ADK `Event` SHALL be serialized as `event.model_dump_json(by_alias=True, exclude_none=True)` and stored as a single AgentCore message. Session IDs SHALL be encoded as `{app_name}__{session_id}` to allow multiple ADK apps to share one memory resource.

The `MemoryClient` SHALL read the session store ID from `AGENTCORE_SESSION_MEMORY_ID` env var or `/gridwise/agentcore/session-memory-id` SSM as fallback.

A `get_session_service()` factory function SHALL be exported from `session.py` for use in `agents.py`.

#### Scenario: Session survives FastAPI restart
- **WHEN** a session with 3 turns is created, FastAPI restarts (in-process state lost), and `get_session` is called with the same session_id
- **THEN** the session is rehydrated from AgentCore with all 3 turns and correct state

#### Scenario: append_event persists to AgentCore
- **WHEN** `append_event(session, event)` is called for a non-partial event
- **THEN** `client.create_event(...)` is called with the JSON-serialized event as the message body

#### Scenario: Partial events are not persisted
- **WHEN** `append_event(session, event)` is called for a streaming partial event (`event.partial = True`)
- **THEN** no `client.create_event(...)` call is made

### Requirement: IAM permissions for FastAPI service role cover both memory resources
The `gridwise-fastapi-service-role` IAM policy in the CDK stack SHALL include `bedrock-agentcore:CreateEvent`, `bedrock-agentcore:ListEvents`, `bedrock-agentcore:GetMemory`, `bedrock-agentcore:RetrieveMemories`, `bedrock-agentcore:GetLastKTurns` on both memory resource ARNs. The existing permissions for `GetMemory`, `PutMemoryRecord`, `SearchMemory`, `DeleteMemoryRecord` SHALL be updated to match the actual SDK method names used by `MemoryClient`.
