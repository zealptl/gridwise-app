## ADDED Requirements

### Requirement: AgentCore Gateway is provisioned via CDK with all 11 tools registered
The system SHALL provision one AgentCore Gateway resource in `gridwise-agent-stack.ts`. All 11 agent tools SHALL be registered on this gateway, each with a name, description, input schema, HTTP backend URL (FastAPI endpoint), and tier access policy.

#### Scenario: Gateway created with all tools at CDK deploy time
- **WHEN** `cdk deploy` runs on the updated `GridwiseAgentStack`
- **THEN** one AgentCore Gateway resource is created and all 11 tools are registered and reachable

#### Scenario: Tool registration includes OpenAPI-quality description
- **WHEN** the gateway returns tool definitions to an ADK MCPToolset
- **THEN** each tool definition includes a `description` field with enough detail for semantic matching (what the tool does, when to use it, what it returns)

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
