## ADDED Requirements

### Requirement: Tool endpoints router exists
The system SHALL expose 11 POST endpoints under `/api/v1/agent/tools/` in `service/app/routers/agent_tools.py`, each delegating to the corresponding function in `tools/*.py`. All routes SHALL require IAM SigV4 request signing (verifying the caller is the `gridwise-fastapi-service-role` Lambda proxy). The router SHALL be registered in `main.py` under the `/api/v1/agent/tools` prefix.

#### Scenario: Known tool called with valid body
- **WHEN** the Lambda proxy sends `POST /api/v1/agent/tools/get-live-session-data` with a valid SigV4 signature
- **THEN** the endpoint calls `get_live_session_data()` and returns its result as JSON with HTTP 200

#### Scenario: Unknown route returns 404
- **WHEN** the Lambda proxy sends a request to a path not matching any of the 11 tool routes
- **THEN** the API returns HTTP 404

#### Scenario: Request without SigV4 signature is rejected
- **WHEN** a caller sends `POST /api/v1/agent/tools/get-weather` without a valid `Authorization: AWS4-HMAC-SHA256` header
- **THEN** the endpoint returns HTTP 403

### Requirement: F1 data tool endpoints
The system SHALL expose `POST /api/v1/agent/tools/get-live-session-data` and `POST /api/v1/agent/tools/get-historical-performance`, delegating to `tools/f1_data.py`.

#### Scenario: Live session data returned
- **WHEN** `get-live-session-data` is called
- **THEN** response includes session metadata, lap times, tyre stints, weather, and race control messages from OpenF1

#### Scenario: Historical performance returned
- **WHEN** `get-historical-performance` is called
- **THEN** response includes season driver standings, constructor standings, and last-3-race results

### Requirement: Intelligence tool endpoints
The system SHALL expose `POST /api/v1/agent/tools/get-weather`, `POST /api/v1/agent/tools/get-odds`, and `POST /api/v1/agent/tools/get-reddit-sentiment`, delegating to `tools/intelligence.py`.

#### Scenario: Weather forecast returned
- **WHEN** `get-weather` is called with `{"circuit_location": "Monaco"}`
- **THEN** response includes a 3-day forecast for the specified location

#### Scenario: Odds data returned
- **WHEN** `get-odds` is called
- **THEN** response includes F1 race winner markets with implied win probabilities

#### Scenario: Reddit sentiment returned
- **WHEN** `get-reddit-sentiment` is called with `{"race_name": "Monaco Grand Prix"}`
- **THEN** response includes recent posts from r/formula1 and r/FantasyF1

### Requirement: Fantasy context tool endpoints
The system SHALL expose `POST /api/v1/agent/tools/get-user-team`, `POST /api/v1/agent/tools/get-current-prices`, `POST /api/v1/agent/tools/get-available-chips`, and `POST /api/v1/agent/tools/get-active-rules`, delegating to `tools/fantasy.py`.

#### Scenario: User team returned
- **WHEN** `get-user-team` is called
- **THEN** response includes current team composition, budget remaining, and transfer count for the authenticated user

#### Scenario: Active rules returned
- **WHEN** `get-active-rules` is called
- **THEN** response lists all active fantasy rules with `rule_type`, `name`, `description`, and human-readable `constraint`

### Requirement: Submission tool endpoints
The system SHALL expose `POST /api/v1/agent/tools/validate-team` and `POST /api/v1/agent/tools/submit-team`, delegating to `tools/submission.py`. `submit-team` SHALL enforce `validated: true` in the request body before proceeding.

#### Scenario: Team validation succeeds
- **WHEN** `validate-team` is called with a valid team payload
- **THEN** response includes `{"valid": true, "violations": []}`

#### Scenario: Submit rejected when not validated
- **WHEN** `submit-team` is called with a body where `validated` is `false` or absent
- **THEN** the endpoint returns HTTP 422 without calling `submit_team()`
