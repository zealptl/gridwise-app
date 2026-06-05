## ADDED Requirements

### Requirement: build_f1_advisor_graph wires AgentCoreSessionService and AgentCoreMemoryService into the Runner
`build_f1_advisor_graph()` in `service/app/agent/agents.py` SHALL construct an ADK `Runner` with:
- `session_service=get_session_service()` — an `AgentCoreSessionService` instance from `session.py`
- `memory_service=AgentCoreMemoryService(memory_id=...)` — reading the memory ID from `AGENTCORE_MEMORY_ID` env var or SSM

This replaces any use of `InMemorySessionService`. The function signature SHALL accept `user_jwt: str | None` and `user_id: str` parameters, where `user_id` is the Cognito `sub` claim extracted from the JWT by the chat endpoint.

#### Scenario: Runner created with AgentCore services
- **WHEN** `build_f1_advisor_graph(user_jwt="eyJ...", user_id="a1b2-sub")` is called
- **THEN** the returned `Runner` has `session_service` of type `AgentCoreSessionService` and `memory_service` of type `AgentCoreMemoryService`

#### Scenario: user_id flows through to memory actor_id
- **WHEN** a session runs for `user_id="a1b2-sub"`
- **THEN** all AgentCore memory reads and writes use `actor_id="a1b2-sub"`

### Requirement: preload_memory tool added to root advisor agent
The root `LlmAgent` (F1 advisor orchestrator) in `agents.py` SHALL include `preload_memory` from `google.adk.tools` in its `tools` list. This causes ADK to automatically inject `<PAST_CONVERSATIONS>` context (extracted from the user's long-term memory) into the orchestrator's prompt before each model call, without any explicit tool invocation by the model.

The orchestrator system prompt SHALL include a section describing how to use `<PAST_CONVERSATIONS>` context: reference extracted user preferences (chip strategy, captain preferences, risk tolerance) when relevant to the current recommendation, but do not fabricate facts not present in the block.

#### Scenario: preload_memory injects context before each turn
- **WHEN** a second chat message is sent for a user with prior session history
- **THEN** the orchestrator receives a `<PAST_CONVERSATIONS>` block in its prompt containing extracted USER_PREFERENCE and SEMANTIC memories before generating its response

#### Scenario: preload_memory does not appear as a function_response in the session
- **WHEN** `preload_memory` runs before a turn
- **THEN** no `function_response` event with name `preload_memory` appears in the session event log

### Requirement: after_agent_callback persists session to long-term memory
The root advisor agent SHALL have `after_agent_callback` set to an async callback that calls `await callback_context.add_session_to_memory()`. This fires once after the orchestrator's turn ends, batching all session events into one `create_event` call and triggering async USER_PREFERENCE + SEMANTIC extraction.

#### Scenario: Session persisted after each completed turn
- **WHEN** the orchestrator finishes a turn (all sub-agents have run, final response emitted)
- **THEN** `add_session_to_memory()` is called exactly once, writing the session's events to AgentCore

#### Scenario: Long-term extraction triggered after session saved
- **WHEN** `add_session_to_memory()` completes
- **THEN** AgentCore asynchronously extracts USER_PREFERENCE records (e.g., "prefers aggressive captain picks") and SEMANTIC facts (e.g., "user accepted Norris as captain in Round 12") within ~60–90 seconds

### Requirement: Chat endpoint extracts user_id (sub claim) from JWT and passes to graph builder
The chat endpoint in `service/app/routers/agent.py` SHALL decode the Cognito JWT to extract the `sub` claim and pass it as `user_id` to `build_f1_advisor_graph(user_jwt=token, user_id=sub)`. The `sub` claim SHALL NOT be looked up via Cognito API — it is present in the JWT payload directly.

#### Scenario: sub claim extracted and forwarded
- **WHEN** `POST /api/v1/agent/chat` is called with a valid Cognito JWT
- **THEN** `build_f1_advisor_graph(user_jwt=<raw_token>, user_id=<sub_claim>)` is called with the correct sub value

#### Scenario: Malformed JWT returns 401 before graph creation
- **WHEN** `POST /api/v1/agent/chat` is called with a JWT that cannot be decoded (expired, tampered)
- **THEN** HTTP 401 is returned before any Runner or session is created

### Requirement: Session ID scoped per chat request
Each call to the chat endpoint SHALL create a new ADK session via `runner.session_service.create_session(app_name="gridwise-advisor", user_id=sub)`. The resulting `session_id` SHALL be used for the entire duration of that chat request. Sessions are not shared across requests; long-term continuity comes from `preload_memory`, not session reuse.

#### Scenario: Each chat request gets its own session
- **WHEN** two concurrent `POST /api/v1/agent/chat` requests arrive for the same user
- **THEN** each request creates a distinct session_id and the sessions do not interfere
