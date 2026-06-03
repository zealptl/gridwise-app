## ADDED Requirements

### Requirement: Root agent reads long-term memory at session start
The system SHALL implement an AgentCore Memory adapter (subclassing ADK's `BaseMemoryService`) that the root `F1FantasyAdvisor` agent uses to retrieve the user's long-term memory at the start of each session.

#### Scenario: Long-term memory loaded before first response
- **WHEN** a new chat session starts for an authenticated user
- **THEN** the root agent calls the memory adapter's `search_memory` method with the user's `user_id` before generating any response, and the results are injected into the agent's context

#### Scenario: No memory found for new user
- **WHEN** a user has no prior long-term memory entries
- **THEN** the memory adapter returns an empty result and the root agent proceeds without memory context

### Requirement: Long-term memory stores user preferences, chip history, and past recommendations
The system SHALL store the following in AgentCore long-term memory per user: stated preferences (e.g., "prefers value picks"), chip usage history, and past team recommendations made by the advisor.

#### Scenario: User preference captured in memory
- **WHEN** the user states a preference during conversation (e.g., "I like aggressive chip usage")
- **THEN** the root agent records this in AgentCore long-term memory associated with the user's `user_id`

#### Scenario: Past recommendation stored after advisor responds
- **WHEN** the advisor produces a team recommendation in a session
- **THEN** the recommendation (drivers, constructors, DRS pick, chip advice, race round) is stored in AgentCore long-term memory for that user

#### Scenario: Chip history available across sessions
- **WHEN** a user starts a new session weeks after using a chip
- **THEN** the root agent's long-term memory includes which chips have been used and at which race rounds

### Requirement: FantasyContextAgent writes fetched data to short-term memory
After successfully fetching the user's team, prices, and chip status, `FantasyContextAgent` SHALL write this data to AgentCore short-term (session-scoped) memory.

#### Scenario: Current team written to short-term memory after fetch
- **WHEN** FantasyContextAgent completes `get_user_team`, `get_current_prices`, and `get_available_chips`
- **THEN** the fetched data is written to AgentCore short-term memory keyed by `session_id`

#### Scenario: Root agent uses short-term memory for follow-up questions
- **WHEN** the user asks a follow-up question about their current team in the same session
- **THEN** the root agent reads from short-term memory instead of re-triggering DataGathering

### Requirement: Memory access is mediated by a dedicated adapter module
The system SHALL isolate all AgentCore Memory API calls behind a `memory.py` module in `service/app/agent/`. No other module SHALL call the AgentCore Memory API directly.

#### Scenario: Memory adapter abstracts AgentCore API surface
- **WHEN** the AgentCore Memory SDK interface changes
- **THEN** only `memory.py` requires updating — agent and tool code is unaffected
