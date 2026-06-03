## ADDED Requirements

### Requirement: F1DataAgent tools fetch live and historical race data
The system SHALL provide `get_live_session_data` and `get_historical_performance` tools assigned to `F1DataAgent`. These tools SHALL call OpenF1 and Jolpica APIs respectively and return structured data for the agent to reason over.

#### Scenario: Live session data fetched from OpenF1
- **WHEN** F1DataAgent calls `get_live_session_data`
- **THEN** the tool returns the latest session's lap times, stints, weather conditions, and race control messages from the OpenF1 API

#### Scenario: Historical performance fetched from Jolpica
- **WHEN** F1DataAgent calls `get_historical_performance`
- **THEN** the tool returns driver standings, constructor form, reliability stats, and circuit-specific history from the Jolpica F1 API

#### Scenario: Tool handles API unavailability gracefully
- **WHEN** OpenF1 or Jolpica is unreachable
- **THEN** the tool returns a structured error response indicating the data source is unavailable, rather than raising an unhandled exception

### Requirement: IntelAgent tools fetch external market and sentiment data
The system SHALL provide `get_weather`, `get_odds`, and `get_reddit_sentiment` tools assigned to `IntelAgent`. These tools SHALL call WeatherAPI, The Odds API, and Reddit OAuth API respectively.

#### Scenario: Weather forecast fetched for race circuit
- **WHEN** IntelAgent calls `get_weather` with a circuit location
- **THEN** the tool returns a multi-day forecast including rain probability, wind speed, and temperature relevant to the race weekend

#### Scenario: Betting odds fetched for race winner market
- **WHEN** IntelAgent calls `get_odds`
- **THEN** the tool returns implied win probabilities for each driver derived from current betting market odds

#### Scenario: Reddit sentiment fetched for recent F1 discussions
- **WHEN** IntelAgent calls `get_reddit_sentiment`
- **THEN** the tool returns a summary of recent r/formula1 and r/FantasyF1 posts relevant to the upcoming race, including mentions of upgrades, penalties, and team form

### Requirement: FantasyContextAgent tools fetch user fantasy state from GridWise
The system SHALL provide `get_user_team`, `get_current_prices`, and `get_available_chips` tools assigned to `FantasyContextAgent`. These tools SHALL read from MongoDB directly via Beanie models.

#### Scenario: User team fetched by user_id
- **WHEN** FantasyContextAgent calls `get_user_team` with the authenticated user's `user_id`
- **THEN** the tool returns the user's current drivers, constructors, DRS Boost selection, budget remaining, and transfer count

#### Scenario: Current market prices fetched
- **WHEN** FantasyContextAgent calls `get_current_prices`
- **THEN** the tool returns the current price for every active driver and constructor from the Driver and Constructor MongoDB collections

#### Scenario: Available chips fetched from user team record
- **WHEN** FantasyContextAgent calls `get_available_chips`
- **THEN** the tool returns which of the six chips (Wildcard, Limitless, No Negative, 3x Boost, Autopilot, Final Fix) remain available for the user this season

### Requirement: SubmissionAgent tools validate and write team changes
The system SHALL provide `validate_team` and `submit_team` tools assigned exclusively to `SubmissionAgent`. `validate_team` SHALL call `RuleEngine` directly. `submit_team` SHALL call `TeamService` directly.

#### Scenario: Proposed team validated against all active rules
- **WHEN** SubmissionAgent calls `validate_team` with a proposed team composition
- **THEN** the tool runs the proposed team through `RuleEngine.validate_team()` and returns a pass/fail result with any violation details

#### Scenario: Valid team submitted and persisted
- **WHEN** SubmissionAgent calls `submit_team` after successful validation
- **THEN** the tool calls `TeamService.create_team()` or `TeamService.update_team()` and returns the persisted team ID

#### Scenario: Invalid team is not submitted
- **WHEN** SubmissionAgent calls `submit_team` with a team that failed validation
- **THEN** the tool returns a validation error and does not persist any changes to MongoDB

### Requirement: All tools registered with AgentCore Gateway
The system SHALL register all tools (across all sub-agents) with a single AgentCore Gateway resource. Sub-agents SHALL acquire their tools from the Gateway at agent initialization.

#### Scenario: Tools available from Gateway at agent startup
- **WHEN** the FastAPI service starts
- **THEN** the ADK agent connects to the AgentCore Gateway and all tools are available to their respective sub-agents without additional setup
