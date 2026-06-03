## ADDED Requirements

### Requirement: AWS Cognito user pool manages user identity
The system SHALL provision an AWS Cognito user pool as the identity provider. Users SHALL register and authenticate through Cognito. The Cognito `sub` claim SHALL be used as the canonical `user_id` throughout the system.

#### Scenario: User registers successfully
- **WHEN** a new user submits valid registration credentials (email + password)
- **THEN** Cognito creates a user record and sends a verification email

#### Scenario: User authenticates and receives JWT
- **WHEN** a registered user submits valid credentials
- **THEN** Cognito returns an ID token (JWT) and access token, with the `sub` claim containing the user's unique identifier

### Requirement: FastAPI validates JWT on protected endpoints
The system SHALL add a JWT validation middleware to FastAPI that validates the Cognito-issued ID token on all `/api/v1/agent/` endpoints. The middleware SHALL extract the `user_id` from the `sub` claim and attach it to the request context.

#### Scenario: Valid JWT grants access to agent endpoints
- **WHEN** a request to `/api/v1/agent/` includes a valid Cognito JWT in the `Authorization: Bearer` header
- **THEN** the middleware validates the token signature against Cognito's public JWKS, extracts `user_id`, and allows the request to proceed

#### Scenario: Missing or invalid JWT returns 401
- **WHEN** a request to `/api/v1/agent/` has no `Authorization` header or an invalid/expired JWT
- **THEN** FastAPI returns HTTP 401 before the request reaches the agent router

#### Scenario: Expired token rejected
- **WHEN** a request includes a Cognito JWT whose `exp` claim is in the past
- **THEN** FastAPI returns HTTP 401 with a message indicating the token has expired

### Requirement: user_id flows through agent session and all tool calls
The system SHALL pass the authenticated `user_id` into the ADK agent session context at session creation time. Tool implementations that access user-specific data (`get_user_team`, `get_available_chips`, `submit_team`) SHALL receive `user_id` from the session context.

#### Scenario: user_id present in all user-specific tool calls
- **WHEN** FantasyContextAgent calls `get_user_team` or SubmissionAgent calls `submit_team`
- **THEN** the tool receives the `user_id` from the ADK session context and uses it to scope the database query or write

#### Scenario: One user cannot access another user's team
- **WHEN** a tool call includes a `user_id` that does not match the authenticated user's session
- **THEN** the tool returns a not-found or unauthorized response without exposing the other user's data

### Requirement: Existing unauthenticated endpoints remain unaffected
The system SHALL NOT apply Cognito JWT validation to existing `/api/v1/teams/`, `/api/v1/drivers/`, `/api/v1/constructors/`, or `/api/v1/rules/` endpoints during this integration. Auth on those routes is out of scope.

#### Scenario: Existing endpoints work without Authorization header
- **WHEN** a request is made to `/api/v1/teams/` without an `Authorization` header
- **THEN** the request proceeds as before — no 401 is returned
