## ADDED Requirements

### Requirement: Tools unavailability is detected before graph execution
The agent graph builder SHALL detect when all sub-agent toolsets are `None` (AgentCore gateway unavailable or package not installed) before running the agent graph.

#### Scenario: All toolsets None triggers fallback path
- **WHEN** `AgentCoreGateway.get_toolset_for_agent` returns `None` for all sub-agents
- **THEN** the `DataGathering` parallel agent SHALL be skipped entirely

#### Scenario: Partial toolset availability does not trigger fallback
- **WHEN** at least one sub-agent toolset is not `None`
- **THEN** the normal `DataGathering` flow SHALL proceed

### Requirement: Sentinel state is injected when tools are unavailable
When the no-tools fallback path is taken, the system SHALL inject sentinel values into the ADK session state before the advisor agent runs, representing each data source as unavailable.

#### Scenario: Sentinel state structure
- **WHEN** the no-tools fallback is triggered
- **THEN** session state SHALL contain keys `f1_data`, `intel`, and `fantasy_context`, each set to `{"available": false, "reason": "AgentCore tools unavailable"}`

#### Scenario: Sentinel injection precedes advisor execution
- **WHEN** sentinel state is injected
- **THEN** the injection SHALL occur before `runner.run_async` is called, with no awaitable between the injection and the run call

### Requirement: Advisor responds with honest error when all data unavailable
When the advisor reads session state and finds all three data slots marked `available: false`, it SHALL respond to the user with a clear, honest explanation rather than hallucinating data or generic advice.

#### Scenario: Honest error response on full unavailability
- **WHEN** all three session state keys (`f1_data`, `intel`, `fantasy_context`) have `available: false`
- **THEN** the advisor SHALL respond stating it cannot provide a recommendation because live data is unavailable, and SHALL NOT produce a team suggestion or hallucinated statistics

#### Scenario: No hallucinated tool calls in response
- **WHEN** sub-agents have no tools (`tools=[]`)
- **THEN** no sub-agent response SHALL contain fake tool-call JSON blocks, `<tool_use>` tags, or fabricated API responses in its output

### Requirement: Session service API calls use correct tuple format
The session service SHALL call `MemoryClient.create_event` with `messages` as a list of `(text, role)` tuples, where `role` is one of `USER`, `ASSISTANT`, `TOOL`, or `OTHER`.

#### Scenario: Correct message format in append_event
- **WHEN** `AgentCoreSessionService.append_event` persists an ADK event
- **THEN** `create_event` SHALL be called with `messages=[(serialized_event, role)]` where `role` is derived from `_role_for_event`

#### Scenario: Role mapping for user events
- **WHEN** `event.author` is `"user"`
- **THEN** the role SHALL be `"USER"`

#### Scenario: Role mapping for tool-response events
- **WHEN** `event.get_function_responses()` returns a non-empty list
- **THEN** the role SHALL be `"TOOL"`

#### Scenario: Role mapping for agent events
- **WHEN** `event.author` is a non-empty string other than `"user"`
- **THEN** the role SHALL be `"ASSISTANT"`

#### Scenario: Role mapping for system/unknown events
- **WHEN** `event.author` is empty or None
- **THEN** the role SHALL be `"OTHER"`

### Requirement: Session service blocking calls are wrapped in asyncio.to_thread
All `MemoryClient` calls within `AgentCoreSessionService` SHALL be executed via `asyncio.to_thread` to avoid blocking the async event loop.

#### Scenario: append_event does not block event loop
- **WHEN** `append_event` calls `MemoryClient.create_event`
- **THEN** the call SHALL be wrapped with `asyncio.to_thread`

#### Scenario: get_session does not block event loop
- **WHEN** `get_session` calls `MemoryClient.list_events`
- **THEN** the call SHALL be wrapped with `asyncio.to_thread`
