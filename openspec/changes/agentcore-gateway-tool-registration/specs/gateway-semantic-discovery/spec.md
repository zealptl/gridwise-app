## ADDED Requirements

### Requirement: ADK sub-agents discover tools via semantic search instead of hardcoded lists
The system SHALL configure each sub-agent's `MCPToolset` to use semantic discovery — passing the sub-agent's description as a query — rather than an explicit `tool_names` list. The gateway SHALL return the top-k most relevant tools that the user is authorized to access.

#### Scenario: F1DataAgent discovers its tools semantically
- **WHEN** `F1DataAgent` initializes its toolset with the query "live F1 session data and historical driver performance"
- **THEN** the gateway returns `get_live_session_data` and `get_historical_performance` as the top results for a free-tier user

#### Scenario: IntelAgent receives fewer tools for free-tier user
- **WHEN** `IntelAgent` initializes with query "external race intelligence: weather, odds, sentiment" and user JWT has `custom:tier: "free"`
- **THEN** the gateway returns no tools (all 3 intelligence tools are premium); IntelAgent proceeds with empty toolset and notes data unavailability in its output

#### Scenario: IntelAgent receives all intelligence tools for premium user
- **WHEN** `IntelAgent` initializes with the same query and user JWT has `custom:tier: "premium"`
- **THEN** the gateway returns `get_weather`, `get_odds`, and `get_reddit_sentiment`

#### Scenario: SubmissionAgent always receives write tools
- **WHEN** `SubmissionAgent` initializes with query "validate and submit F1 fantasy team"
- **THEN** the gateway returns `validate_team` and `submit_team` for any tier (both are free-tier tools)

### Requirement: gateway.py passes user JWT to MCPToolset for every agent session
The system SHALL accept a user JWT string in `AgentCoreGateway` and inject it as a bearer token header on every `MCPToolset` connection, so the gateway can apply tier filtering per user.

#### Scenario: JWT injected on MCPToolset connection
- **WHEN** `gateway.get_toolset_for_agent(agent_name, query, jwt)` is called
- **THEN** the resulting `MCPToolset` sends `Authorization: Bearer <jwt>` on all MCP protocol requests to the gateway

#### Scenario: Missing JWT falls back to anonymous (no premium tools)
- **WHEN** `AgentCoreGateway` is initialized without a JWT (e.g. local dev)
- **THEN** `MCPToolset` connects without an Authorization header; gateway returns only free-tier tools (or empty set if auth is required)

### Requirement: Sub-agent instructions include detailed reasoning guidance
The system SHALL provide each sub-agent with instructions that describe: which data to collect, how to handle partial failures, what memory key to write, and what format the output summary should take.

#### Scenario: F1DataAgent handles OpenF1 API unavailability
- **WHEN** `get_live_session_data` returns `{"error": "OpenF1 API unavailable", "available": false}`
- **THEN** `F1DataAgent` writes the error to session memory under key `f1_data` and includes `"available": false` so the root agent can reduce confidence accordingly

#### Scenario: IntelAgent runs with no tools (free-tier user)
- **WHEN** `IntelAgent` receives an empty toolset
- **THEN** it writes `{"available": false, "reason": "intelligence tools require premium tier"}` to session memory under key `intel` without raising an error

#### Scenario: FantasyContextAgent writes all context fields to session memory
- **WHEN** `FantasyContextAgent` completes its data gathering
- **THEN** session memory key `fantasy_context` contains `team`, `prices`, `chips`, and `rules` fields, with any unavailable fields set to `null` with an `error` sub-key
