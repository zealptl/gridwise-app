## ADDED Requirements

### Requirement: Root agent orchestrates conversation
The system SHALL provide a root `F1FantasyAdvisor` LlmAgent (Claude via Bedrock) that maintains conversational state, reads AgentCore long-term memory at session start, and dynamically delegates to sub-agents based on user intent.

#### Scenario: Advisor reads long-term memory on session start
- **WHEN** a new chat session begins for an authenticated user
- **THEN** the root agent reads the user's long-term memory (preferences, chip history, past recommendations) from AgentCore before responding

#### Scenario: Advisor delegates data gathering dynamically
- **WHEN** the user requests a team recommendation or asks about their prospects for an upcoming race
- **THEN** the root agent transfers control to the DataGathering ParallelAgent before synthesizing a response

#### Scenario: Advisor handles follow-up questions without re-gathering
- **WHEN** the user asks a follow-up question after data has already been gathered in the session
- **THEN** the root agent responds using short-term memory without re-triggering DataGathering

### Requirement: Parallel data gathering sub-agents
The system SHALL provide a `DataGathering` ParallelAgent that runs `F1DataAgent`, `IntelAgent`, and `FantasyContextAgent` concurrently, with their results merged into the session context before the root agent synthesizes a recommendation.

#### Scenario: Three sub-agents run concurrently
- **WHEN** the root agent delegates to DataGathering
- **THEN** F1DataAgent, IntelAgent, and FantasyContextAgent all start execution simultaneously and the root agent waits for all three to complete

#### Scenario: Partial data gathering failure is surfaced
- **WHEN** one sub-agent fails (e.g., OpenF1 API is down)
- **THEN** the root agent acknowledges the missing data source and provides a recommendation with reduced confidence, rather than failing entirely

### Requirement: Write operations isolated to SubmissionAgent
The system SHALL ensure only `SubmissionAgent` has access to write-capable tools. `F1DataAgent`, `IntelAgent`, and `FantasyContextAgent` SHALL be read-only.

#### Scenario: Submission requires explicit user confirmation
- **WHEN** the root agent produces a team recommendation
- **THEN** it SHALL NOT delegate to SubmissionAgent until the user explicitly confirms they want to apply the recommendation

#### Scenario: Validation runs before submission
- **WHEN** SubmissionAgent is invoked with a proposed team
- **THEN** it SHALL call `validate_team` before `submit_team`, and SHALL NOT submit if validation fails

### Requirement: Agent graph is embedded in FastAPI process
The system SHALL run the ADK agent Runner within the GridWise FastAPI service — not as a separate process or Lambda — with tools having direct access to MongoDB models and service classes.

#### Scenario: Tool calls bypass HTTP for internal data
- **WHEN** FantasyContextAgent calls `get_user_team`
- **THEN** the tool queries MongoDB directly via Beanie models without making an HTTP request to the GridWise API

#### Scenario: Agent runner is async-compatible with FastAPI
- **WHEN** a chat request arrives at the FastAPI agent endpoint
- **THEN** the ADK Runner executes within the async event loop without blocking other API requests
