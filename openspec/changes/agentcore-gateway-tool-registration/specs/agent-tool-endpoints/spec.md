## ADDED Requirements

### Requirement: FastAPI exposes one HTTP endpoint per agent tool
The system SHALL provide a dedicated `POST` endpoint for each of the 11 agent tools under the `/agent/tools/` path prefix. Each endpoint SHALL accept a JSON body matching that tool's input schema and return a JSON response.

#### Scenario: F1 data tool endpoint called by gateway
- **WHEN** the AgentCore Gateway invokes `POST /agent/tools/get-live-session-data`
- **THEN** the endpoint calls the existing `get_live_session_data()` implementation and returns its structured dict response as JSON

#### Scenario: Internal tool endpoint uses existing service layer
- **WHEN** the AgentCore Gateway invokes `POST /agent/tools/get-user-team` with a `user_id` in the request body
- **THEN** the endpoint calls `get_f1_fantasy_team()` via the existing Beanie model layer without opening a new DB connection

#### Scenario: External API tool is proxied through FastAPI
- **WHEN** the AgentCore Gateway invokes `POST /agent/tools/get-weather` with a `circuit_location` parameter
- **THEN** the FastAPI endpoint calls the `get_weather()` function which proxies to WeatherAPI and returns the forecast

#### Scenario: Tool endpoint returns structured error on upstream failure
- **WHEN** an external API (OpenF1, WeatherAPI, etc.) is unreachable during a tool endpoint call
- **THEN** the endpoint returns HTTP 200 with a structured JSON error body (`{"error": "...", "available": false}`) rather than propagating an HTTP 5xx

### Requirement: Tool endpoints require service-level IAM authentication
The system SHALL restrict all `/agent/tools/*` endpoints to requests authenticated via AWS IAM SigV4 — they are not user-facing endpoints and SHALL NOT be accessible with a Cognito JWT alone.

#### Scenario: Unauthenticated request to tool endpoint is rejected
- **WHEN** a request reaches `/agent/tools/get-live-session-data` without a valid IAM SigV4 signature
- **THEN** the endpoint returns HTTP 403

#### Scenario: AgentCore Gateway can invoke tool endpoints
- **WHEN** the AgentCore Gateway invokes any `/agent/tools/*` endpoint using the FastAPI service's IAM role
- **THEN** the request is authenticated and the tool executes

### Requirement: Submission tool endpoints enforce validate-before-submit ordering
The system SHALL ensure that `POST /agent/tools/submit-team` returns an error if called without a prior successful `validate_team` result in the request body.

#### Scenario: Submit called without validation result is rejected
- **WHEN** `POST /agent/tools/submit-team` is called with a team body that has no `validated: true` field
- **THEN** the endpoint returns `{"error": "Team must be validated before submission", "valid": false}` without persisting any changes

#### Scenario: Submit called with valid team proceeds
- **WHEN** `POST /agent/tools/submit-team` is called with a team body that includes `validated: true`
- **THEN** the endpoint calls `TeamService.create_team()` or `update_team()` and returns `{"success": true, "team_id": "..."}`
