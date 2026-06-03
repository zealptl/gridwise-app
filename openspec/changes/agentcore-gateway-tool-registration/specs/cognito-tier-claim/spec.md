## ADDED Requirements

### Requirement: Cognito user pool has a custom tier attribute
The system SHALL add a `custom:tier` attribute to the Cognito user pool. The attribute SHALL be a string with allowed values `free` and `premium`. New users SHALL be assigned `free` by default at registration.

#### Scenario: New user registered with free tier
- **WHEN** a new user registers via the `/auth/register` endpoint
- **THEN** their Cognito user record has `custom:tier` set to `"free"`

#### Scenario: Tier attribute present in Cognito JWT
- **WHEN** a registered user authenticates and receives a Cognito ID token
- **THEN** the token payload contains the claim `custom:tier` with value `"free"` or `"premium"`

### Requirement: Auth module extracts tier claim from JWT
The system SHALL provide a utility function in `auth.py` that parses a Cognito JWT and returns the `custom:tier` value. The function SHALL return `"free"` as the default if the claim is absent.

#### Scenario: Tier extracted from valid JWT
- **WHEN** `get_user_tier(jwt_token)` is called with a valid Cognito JWT containing `custom:tier: "premium"`
- **THEN** the function returns `"premium"`

#### Scenario: Missing claim defaults to free
- **WHEN** `get_user_tier(jwt_token)` is called with a JWT that has no `custom:tier` claim
- **THEN** the function returns `"free"`

### Requirement: Chat endpoint forwards user JWT to agent session
The system SHALL extract the raw Cognito JWT from the incoming chat request's `Authorization` header and pass it to `AgentCoreGateway` when building the agent session, so the gateway can apply tier-based tool filtering for that user.

#### Scenario: JWT forwarded from chat request to gateway
- **WHEN** a user sends a chat message with a valid Cognito JWT in the `Authorization: Bearer <token>` header
- **THEN** the FastAPI chat endpoint passes that same JWT string to `AgentCoreGateway(jwt=token)` before building the agent graph

#### Scenario: Chat request without JWT returns 401
- **WHEN** a request arrives at the chat endpoint without an `Authorization` header
- **THEN** the endpoint returns HTTP 401 before attempting to build the agent session
