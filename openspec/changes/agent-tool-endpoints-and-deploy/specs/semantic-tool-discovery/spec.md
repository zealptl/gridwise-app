## ADDED Requirements

### Requirement: AgentCoreGateway accepts and stores user JWT
`AgentCoreGateway.__init__` SHALL accept an optional `jwt: str | None = None` parameter and store it as an instance attribute for use during tool discovery.

#### Scenario: JWT stored on init
- **WHEN** `AgentCoreGateway(jwt="eyJhbGci...")` is instantiated
- **THEN** `gateway.jwt` equals the provided token

### Requirement: Semantic discovery replaces tool_names registry
`get_toolset_for_agent` SHALL use a `discovery_query` (the sub-agent's description string) to request matching tools from the AgentCore Gateway instead of looking up tool names from a `TOOL_REGISTRY` dict. The `MCPToolset` connection SHALL inject `Authorization: Bearer <jwt>` as a header so the gateway can enforce `custom:tier` access policies. `TOOL_REGISTRY` and the `get_toolset` wrapper SHALL be removed.

#### Scenario: Free-tier user receives 8 tools
- **WHEN** `get_toolset_for_agent` is called with a `discovery_query` and a free-tier JWT
- **THEN** the returned toolset contains 8 tools (intelligence tools excluded by gateway tier policy)

#### Scenario: Premium-tier user receives all 11 tools
- **WHEN** `get_toolset_for_agent` is called with a `discovery_query` and a premium JWT
- **THEN** the returned toolset contains all 11 tools

#### Scenario: Missing JWT results in empty toolset
- **WHEN** `get_toolset_for_agent` is called with `jwt=None`
- **THEN** the returned toolset is empty and no exception is raised

### Requirement: verify_gateway_connection uses semantic query
`verify_gateway_connection` SHALL test connectivity using a sample semantic query rather than a named tool lookup, and SHALL confirm at least one tool is returned.

#### Scenario: Connectivity verified with semantic query
- **WHEN** `verify_gateway_connection()` is called after CDK deploy
- **THEN** no exception is raised and a log message confirms the number of tools returned

### Requirement: build_f1_advisor_graph accepts and propagates user_jwt
`build_f1_advisor_graph()` SHALL accept `user_jwt: str | None` and pass it to `AgentCoreGateway(jwt=user_jwt)`. Each sub-agent builder (`_build_f1_data_agent`, `_build_intel_agent`, `_build_fantasy_context_agent`, `_build_submission_agent`) SHALL pass a `discovery_query` derived from the sub-agent description and SHALL NOT use a hardcoded `tool_names` list.

#### Scenario: JWT propagated to gateway from graph builder
- **WHEN** `build_f1_advisor_graph(user_jwt="tok")` is called
- **THEN** the `AgentCoreGateway` instance used by all sub-agents has `jwt="tok"`

### Requirement: Chat endpoint forwards raw JWT to agent graph
The chat endpoint SHALL extract the raw JWT string from the `Authorization: Bearer <token>` header and pass it as `user_jwt` to `build_f1_advisor_graph()`. If the `Authorization` header is absent, the endpoint SHALL return HTTP 401 before creating an agent session.

#### Scenario: JWT forwarded from chat request to graph
- **WHEN** `POST /api/v1/agent/chat` is called with a valid `Authorization: Bearer <token>` header
- **THEN** `build_f1_advisor_graph(user_jwt=<token>)` is called with the raw token string

#### Scenario: Missing Authorization header returns 401
- **WHEN** `POST /api/v1/agent/chat` is called without an `Authorization` header
- **THEN** the endpoint returns HTTP 401 before creating any agent session
