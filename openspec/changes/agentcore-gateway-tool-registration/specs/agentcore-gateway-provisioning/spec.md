## ADDED Requirements

### Requirement: AgentCore Gateway is provisioned via CDK with all 11 tools registered
The system SHALL provision one AgentCore Gateway resource in `gridwise-agent-stack.ts`. All 11 agent tools SHALL be registered on this gateway, each with a name, description, input schema, HTTP backend URL (FastAPI endpoint), and tier access policy.

#### Scenario: Gateway created with all tools at CDK deploy time
- **WHEN** `cdk deploy` runs on the updated `GridwiseAgentStack`
- **THEN** one AgentCore Gateway resource is created and all 11 tools are registered and reachable

#### Scenario: Tool registration includes OpenAPI-quality description
- **WHEN** the gateway returns tool definitions to an ADK MCPToolset
- **THEN** each tool definition includes a `description` field with enough detail for semantic matching (what the tool does, when to use it, what it returns)

### Requirement: Each tool description follows a standard four-part format
Every tool registered on the gateway SHALL have a description that covers: (1) what the tool does in one sentence, (2) when an agent should call it, (3) what data it returns, and (4) how to handle failure responses. Thin one-line descriptions are not acceptable — the description is the primary signal the gateway uses for semantic tool selection.

#### Scenario: Tool description is rich enough for semantic retrieval
- **WHEN** a sub-agent sends the semantic query "live F1 session data for the current race weekend"
- **THEN** the gateway returns `get_live_session_data` because its description explicitly mentions live session data, lap times, stints, and race weekend context

#### Scenario: Tool description distinguishes similar tools
- **WHEN** a sub-agent sends the query "current driver and constructor prices"
- **THEN** the gateway returns `get_current_prices` and NOT `get_historical_performance`, because the descriptions clearly distinguish live pricing data from historical race results

### Requirement: Tool descriptions are defined as follows for all 11 tools

The system SHALL register each tool with the exact description text specified below. These descriptions are the source of truth for gateway registration and SHALL NOT be replaced with shorter summaries.

**get_live_session_data**
> Fetches real-time F1 session data from the OpenF1 API for the latest race weekend session (practice, qualifying, sprint, or race). Call this first in any recommendation flow to get current lap times, tyre stints, on-track weather conditions, and race control messages (flags, safety car, penalties). Returns a structured dict with keys: `session`, `laps`, `stints`, `weather`, `race_control`. If OpenF1 is unavailable, returns `{"error": "OpenF1 API unavailable", "available": false}` — treat this as reduced-confidence input, do not abort the recommendation.

**get_historical_performance**
> Fetches season-to-date historical performance data from the Jolpica/Ergast F1 API. Use this to understand driver and constructor championship standings, recent race results, and form trends that live session data cannot provide. Returns a structured dict with keys: `driver_standings`, `constructor_standings`, `recent_results`. Individual endpoint failures return `{"error": "..."}` under the relevant key — use whatever data is available and note any gaps.

**get_weather**
> Fetches a 3-day weather forecast for a given F1 circuit location from WeatherAPI. Use this to assess rain probability, wind conditions, and temperature shifts that affect tyre strategy and car setup. Pass the circuit city or country as `circuit_location` (e.g. "Monaco", "Silverstone"). Returns `location`, `forecast` (array of daily forecasts), and `race_day_forecast` (last day in the forecast window). PREMIUM TOOL — only available to premium-tier users. On API failure, returns `{"error": "WeatherAPI unavailable"}`.

**get_odds**
> Fetches current Formula 1 race winner betting odds from The Odds API and converts them to implied win probabilities per driver. Use this as a market-consensus signal to validate or challenge your own predictions — high implied probability for a driver suggests broad agreement across bookmakers. Returns `event` (race name and date) and `probabilities` (dict mapping driver name to implied probability 0–1). PREMIUM TOOL — only available to premium-tier users. On API failure, returns `{"error": "Odds API unavailable"}`.

**get_reddit_sentiment**
> Searches recent posts in r/formula1 and r/FantasyF1 for community discussion about a specific race or driver. Use this to surface grassroots intelligence: upgrade rumours, mechanical concerns, driver form commentary, and fantasy community consensus picks that may not appear in official data. Pass the race name or driver name as `race_name`. Returns `r_formula1` posts, `r_FantasyF1` posts, and a `sentiment_summary` string. PREMIUM TOOL — only available to premium-tier users. On API failure, returns `{"error": "Reddit API unavailable"}`.

**get_user_team**
> Retrieves the authenticated user's current F1 Fantasy team from the GridWise database. Use this at the start of every recommendation to understand the user's existing picks before suggesting changes. Requires `user_id` in session state. Returns the user's current drivers, constructors, DRS Boost selection, total team cost, budget remaining, and transfer count used this race week.

**get_current_prices**
> Returns the live market price for every active F1 driver and constructor in the GridWise fantasy game. Use this alongside the user's current team to calculate transfer costs and budget headroom for proposed changes. Returns a dict with `drivers` and `constructors` arrays, each entry containing `id`, `name`, `team`, and `price` in millions.

**get_available_chips**
> Returns the chip/booster availability for the authenticated user this season. Use this before making any chip-dependent recommendation (e.g. Limitless, Wildcard). Requires `user_id` in session state. Returns a dict mapping each of the six chip names (`wildcard`, `limitless`, `no_negative`, `triple_boost`, `autopilot`, `final_fix`) to a boolean indicating whether it has been used.

**get_active_rules**
> Fetches all currently active fantasy rules and constraints from the GridWise rules engine. Call this before constructing or validating any team recommendation to ensure compliance. Returns `{"rules": [...]}` where each rule has `rule_type`, `name`, `description`, and a human-readable `constraint` string (e.g. "Total team cost must not exceed 100M", "Team must include exactly 5 drivers and 2 constructors").

**validate_team**
> Validates a proposed fantasy team composition against all active GridWise rules. MUST be called before `submit_team` — submission without prior validation will be rejected. Pass the full proposed team as a dict with `team_name`, `drivers` (list of driver dicts with `driver_id`, `driver_name`, `team_name`, `price`), `constructors`, `drs_boost_driver_id`, and `budget_cap`. Returns `{"valid": true, "violations": []}` on success, or `{"valid": false, "violations": [...]}` with violation details on failure. Never submit a team that failed validation.

**submit_team**
> Persists the user's validated fantasy team to the GridWise database. Only call this after `validate_team` returns `valid: true` AND the user has given explicit confirmation they want to apply the recommendation. Requires `user_id` in session state and the validated team dict. Automatically creates a new team or updates the existing active team for the current season. Returns `{"success": true, "team_id": "..."}` on success or `{"error": "..."}` on failure.

#### Scenario: All 11 tool descriptions are present at gateway registration
- **WHEN** `aws bedrock-agentcore list-gateway-tools` is run after CDK deploy
- **THEN** all 11 tools are listed and each has a non-empty `description` field matching the text defined above

### Requirement: Gateway enforces tier-based tool access using JWT claims
The system SHALL configure tier-based access policies on the gateway such that free-tier tools are accessible with any valid JWT, and premium tools require `custom:tier: "premium"` in the JWT claims.

#### Scenario: Free user cannot access premium tools
- **WHEN** an MCPToolset connection is established with a JWT containing `custom:tier: "free"`
- **THEN** the gateway returns only the 8 free-tier tools in semantic discovery results; `get_weather`, `get_odds`, and `get_reddit_sentiment` are not returned

#### Scenario: Premium user accesses all tools
- **WHEN** an MCPToolset connection is established with a JWT containing `custom:tier: "premium"`
- **THEN** the gateway returns all 11 tools in semantic discovery results

#### Scenario: Request without JWT is rejected at gateway
- **WHEN** an MCPToolset connection is attempted without a bearer token
- **THEN** the gateway returns an authentication error and no tools are served

### Requirement: Gateway uses IAM for service-to-FastAPI authentication
The system SHALL configure the gateway to call FastAPI tool endpoints using the `gridwise-fastapi-service-role` IAM role, so FastAPI can verify the caller is the gateway and not an external client.

#### Scenario: Gateway calls FastAPI tool endpoint with IAM signature
- **WHEN** the gateway invokes a tool handler (e.g. `POST /agent/tools/get-live-session-data`)
- **THEN** the HTTP request is signed with the FastAPI service IAM role credentials (SigV4)

### Requirement: Gateway endpoint URL is stored in SSM Parameter Store
The system SHALL store the deployed gateway endpoint URL in SSM at `/gridwise/agentcore/gateway-endpoint` so `gateway.py` can load it at runtime without hardcoding.

#### Scenario: Gateway URL available in SSM after deploy
- **WHEN** CDK deploy completes
- **THEN** the gateway endpoint URL is written to `/gridwise/agentcore/gateway-endpoint` in SSM Parameter Store

#### Scenario: gateway.py loads endpoint from SSM on startup
- **WHEN** the FastAPI service starts and `AgentCoreGateway.__init__()` runs
- **THEN** it reads `/gridwise/agentcore/gateway-endpoint` from SSM and stores it as `self.endpoint_url`
