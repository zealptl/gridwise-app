## ADDED Requirements

### Requirement: Single AgentCore Gateway hosts all agent tools
The system SHALL provision one AgentCore Gateway resource and register all tools from all sub-agents (`F1DataAgent`, `IntelAgent`, `FantasyContextAgent`, `SubmissionAgent`) within it. Sub-agents SHALL connect to this Gateway as an MCP toolset.

#### Scenario: All tools reachable from one Gateway endpoint
- **WHEN** any sub-agent needs to call a tool
- **THEN** the tool is invoked through the single AgentCore Gateway endpoint without sub-agent-specific routing configuration

#### Scenario: Gateway authenticates sub-agent tool calls via IAM
- **WHEN** a sub-agent calls a tool through the Gateway
- **THEN** the call is authenticated using the FastAPI service's IAM role — no separate API key is required

### Requirement: Gateway registration is managed by a dedicated module
The system SHALL isolate all AgentCore Gateway client code and tool registration behind a `gateway.py` module in `service/app/agent/`. Agent initialization code SHALL import tool sets from this module, not interact with the Gateway directly.

#### Scenario: Tools loaded from Gateway at agent initialization
- **WHEN** the FastAPI service starts and initializes the ADK agent graph
- **THEN** `gateway.py` connects to the AgentCore Gateway, retrieves the registered tool definitions, and returns them as ADK-compatible tool objects for each sub-agent

#### Scenario: Gateway module isolates SDK changes
- **WHEN** the AgentCore Gateway SDK interface changes
- **THEN** only `gateway.py` requires updating — `agents.py` and tool implementation files are unaffected

### Requirement: External API credentials stored in AWS Secrets Manager
API credentials for external tools (WeatherAPI, Odds API, Reddit OAuth) SHALL be stored in AWS Secrets Manager and fetched at Lambda/tool invocation time. They SHALL NOT be stored in environment variables or committed to source control.

#### Scenario: Tool fetches credentials from Secrets Manager at runtime
- **WHEN** IntelAgent calls `get_weather`, `get_odds`, or `get_reddit_sentiment`
- **THEN** the tool retrieves the relevant API credential from Secrets Manager before making the external API call

#### Scenario: Missing credential surfaces a clear error
- **WHEN** a Secrets Manager secret is missing or inaccessible
- **THEN** the tool returns a structured error indicating which credential is missing, not a generic exception
