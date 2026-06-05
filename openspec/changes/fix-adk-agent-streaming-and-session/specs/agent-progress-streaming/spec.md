## ADDED Requirements

### Requirement: Only root agent text reaches the user
The streaming layer SHALL forward `TEXT_MESSAGE_CONTENT` AG-UI events only for ADK events whose `author` matches the root advisor agent name. Events from sub-agents SHALL NOT produce `TEXT_MESSAGE_CONTENT`.

#### Scenario: Sub-agent text is suppressed
- **WHEN** an ADK event is emitted with `author` set to a sub-agent name (e.g., `F1DataAgent`, `IntelAgent`, `FantasyContextAgent`)
- **THEN** the event SHALL NOT be forwarded as `TEXT_MESSAGE_CONTENT` to the client

#### Scenario: Advisor text is forwarded
- **WHEN** an ADK event is emitted with `author` equal to `F1FantasyAdvisor`
- **THEN** all text parts of that event SHALL be forwarded as `TEXT_MESSAGE_CONTENT` to the client

### Requirement: Sub-agent activity emits STATE_SNAPSHOT progress events
The streaming layer SHALL emit a `STATE_SNAPSHOT` AG-UI event for each sub-agent ADK event, containing a structured `agentProgress` payload with the sub-agent's current status.

#### Scenario: Sub-agent working state emitted
- **WHEN** a text or function-call ADK event is emitted by a sub-agent
- **THEN** a `STATE_SNAPSHOT` event SHALL be emitted with `agentProgress.<agentKey>` set to `"working"`

#### Scenario: Sub-agent completion state emitted
- **WHEN** the last ADK event for a sub-agent is processed (no further events from that author in the turn)
- **THEN** a `STATE_SNAPSHOT` event SHALL be emitted with `agentProgress.<agentKey>` set to `"done"`

#### Scenario: Progress payload structure
- **WHEN** a `STATE_SNAPSHOT` is emitted for sub-agent progress
- **THEN** the snapshot SHALL include a top-level `agentProgress` key with sub-keys for each sub-agent: `f1DataAgent`, `intelAgent`, `fantasyContextAgent`

### Requirement: Agent name is defined as a module-level constant
The root advisor agent name used in both the `LlmAgent` constructor and the streaming filter SHALL be sourced from a single module-level constant to prevent silent divergence.

#### Scenario: Name constant used in agent construction
- **WHEN** `build_f1_advisor_graph` constructs the `F1FantasyAdvisor` LlmAgent
- **THEN** the `name` kwarg SHALL reference the module-level constant, not a string literal

#### Scenario: Name constant used in event filter
- **WHEN** `_adk_event_to_ag_ui` or `_stream_ag_ui` filters events by author
- **THEN** the comparison SHALL reference the same module-level constant
