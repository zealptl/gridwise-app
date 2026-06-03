## ADDED Requirements

### Requirement: POST /api/v1/agent/chat streams agent responses via SSE
The system SHALL expose a `POST /api/v1/agent/chat` endpoint that accepts a user message and `session_id`, runs the ADK agent, and streams the response as Server-Sent Events (SSE) using FastAPI's `StreamingResponse`.

#### Scenario: Chat request returns SSE stream
- **WHEN** an authenticated user posts `{ "message": "What team should I pick?", "session_id": "abc123" }` to `/api/v1/agent/chat`
- **THEN** the endpoint returns `Content-Type: text/event-stream` and streams agent response chunks as SSE events until the agent turn completes

#### Scenario: Session_id maintains multi-turn conversation
- **WHEN** the same `session_id` is used across multiple requests
- **THEN** the ADK Runner resumes the existing session and the agent has access to prior conversation turns

#### Scenario: New session_id starts a fresh conversation
- **WHEN** a request arrives with a `session_id` not seen before
- **THEN** the ADK Runner creates a new session, loads long-term memory, and begins a fresh conversation

#### Scenario: Unauthenticated chat request rejected
- **WHEN** a request to `/api/v1/agent/chat` lacks a valid Cognito JWT
- **THEN** the endpoint returns HTTP 401 before the agent runner is invoked

### Requirement: POST /api/v1/agent/sessions creates a new session
The system SHALL expose a `POST /api/v1/agent/sessions` endpoint that creates a new ADK session for the authenticated user and returns a `session_id` for use in subsequent chat requests.

#### Scenario: Session created and ID returned
- **WHEN** an authenticated user posts to `/api/v1/agent/sessions`
- **THEN** the endpoint returns `{ "session_id": "<uuid>" }` and the session is registered with the ADK Runner

### Requirement: Agent router is isolated in service/app/routers/agent.py
The system SHALL implement the agent API in a dedicated `agent.py` router registered under the `/api/v1/agent` prefix. The router SHALL be the only FastAPI code that instantiates or interacts with the ADK Runner.

#### Scenario: Agent router registered in main.py
- **WHEN** the FastAPI application starts
- **THEN** the agent router is mounted at `/api/v1/agent` alongside existing routers, with no changes to other router configurations

### Requirement: Agent errors return structured JSON, not raw exceptions
The system SHALL catch agent runner exceptions and return structured JSON error responses rather than propagating raw Python exceptions to the SSE stream or HTTP response.

#### Scenario: Agent inference error returns 500 with message
- **WHEN** the ADK Runner raises an unhandled exception during a chat request
- **THEN** the SSE stream closes and the client receives a final SSE event with `event: error` and a JSON body containing a human-readable message
