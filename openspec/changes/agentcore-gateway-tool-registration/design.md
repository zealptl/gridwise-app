## Context

The F1 Fantasy Advisor is built on Google ADK with sub-agents (`F1DataAgent`, `IntelAgent`, `FantasyContextAgent`, `SubmissionAgent`) that acquire tools via `MCPToolset` from an AgentCore Gateway. Today the gateway is not deployed, `MCPToolset` returns `None`, and all sub-agents run with an empty tools list. The Python tool implementations exist in `service/app/agent/tools/*.py` but are not reachable by the agent graph.

All tool implementations either read from MongoDB/internal services (fantasy context, rules, submission) or call external APIs (OpenF1, Jolpica, WeatherAPI, Odds API, Reddit). The FastAPI service already has DB connection pooling and service layer classes — duplicating this in standalone Lambdas would create a separate connection path to maintain.

## Goals / Non-Goals

**Goals:**
- All 11 tools callable end-to-end through AgentCore Gateway → FastAPI
- Gateway enforces tier-based access (`free` | `premium`) at the tool level using the Cognito JWT
- ADK sub-agents discover tools via semantic search — no hardcoded `tool_names` lists
- Sub-agent instructions enriched with reasoning guidance, output format, and failure handling
- Architecture scales to 50+ tools without changes to `agents.py`

**Non-Goals:**
- ML prediction engine or team optimizer tools (not in current tool set)
- Per-tool rate limiting (future work)
- Tool versioning or deprecation flow
- Changes to the chat API request/response contract

## Decisions

### Decision 1: All tools as FastAPI endpoints (not Lambdas)

Internal tools (`get_user_team`, `validate_team`, `submit_team`, etc.) depend on Beanie ODM models and the `RuleEngine`/`TeamService` classes. Standing these up in isolated Lambdas would require a separate MongoDB connection pool, duplicated service code, and a new deployment artifact. The FastAPI service already owns this layer.

External API tools (`get_weather`, `get_odds`, `get_reddit_sentiment`) are pure HTTP clients — they could be Lambdas, but keeping them in FastAPI means one backend, one deployment, one set of secrets access patterns.

**Alternative considered**: Lambda per tool. Rejected: doubles the infrastructure surface, duplicates DB connection logic, complicates local development.

### Decision 2: Semantic discovery over hardcoded tool_names

Current code maps each sub-agent to an explicit list of tool names. With semantic discovery:
- The gateway filters tools by user tier from JWT
- Sub-agents send a semantic query (derived from their `description` field) and receive the top-k matching tools
- Adding new tools to the gateway automatically makes them discoverable — no `agents.py` changes

**Alternative considered**: Keep explicit `tool_names` per agent but add rich descriptions to gateway registrations. Rejected: doesn't scale to 50+ tools, requires manual `agents.py` updates per new tool, doesn't benefit from tier filtering at discovery time.

### Decision 3: Cognito `custom:tier` claim in JWT

The gateway needs the user's tier at tool-discovery time without a DB lookup. Baking it into the JWT as `custom:tier` means the gateway can enforce access policies stateless. The claim is set at registration (default: `free`) and updated when a user upgrades.

**Alternative considered**: Gateway looks up tier from a separate user service call. Rejected: adds latency on every tool-discovery request, introduces a dependency the gateway shouldn't have.

### Decision 4: Single `/agent/tools/*` router, one endpoint per tool

Each tool gets its own route (e.g. `POST /agent/tools/get-live-session-data`). The AgentCore Gateway calls these endpoints as the tool handler. This keeps routing explicit and makes each tool independently testable.

**Alternative considered**: Single dispatch endpoint (`POST /agent/tools/{tool_name}`). Rejected: harder to document in OpenAPI, harder to set per-tool auth middleware, harder to trace in logs.

### Decision 5: MCPToolset receives user JWT via header injection

When the FastAPI chat endpoint initializes the ADK agent session, it passes the user's raw Cognito JWT. The `gateway.py` module injects it as a bearer token header on the `MCPToolset` connection. The gateway authenticates the service (IAM) and authorizes tool access (JWT tier claim) separately.

## Risks / Trade-offs

- **AgentCore CDK API is new** → The `AWS::BedrockAgentCore::Gateway` CloudFormation resource schema is still evolving. Properties may differ from docs. Mitigation: use CDK `CfnResource` with explicit type, pin SDK versions, test deploy early.
- **Semantic discovery non-determinism** → The same sub-agent may receive slightly different tool sets across requests if gateway embeddings change. Mitigation: sub-agent instructions are written to handle tool unavailability gracefully; `SubmissionAgent` always gets `validate_team` + `submit_team` as anchors.
- **JWT expiry mid-session** → Long agent sessions may outlive a Cognito token. Mitigation: chat endpoint refreshes token before creating agent session; gateway returns 401 on expiry which surfaces as a tool error.
- **FastAPI as single point of failure** → All tool calls route through FastAPI. If it's slow, all tools are slow. Mitigation: tool endpoints are thin — they delegate to existing service layer with no added logic.

## Migration Plan

1. Deploy Cognito custom attribute (`custom:tier`) — additive, no existing users affected
2. Deploy FastAPI tool router — new routes, no existing routes changed
3. Deploy AgentCore Gateway CDK — new resource, no existing infra changed
4. Register all 11 tools on gateway with descriptions + tier policies
5. Update `gateway.py` and `agents.py` — deployed with FastAPI service
6. Smoke test: free user → 8 tools visible; premium user → 11 tools visible
7. **Rollback**: revert `gateway.py` to previous stub (empty toolsets) — agents degrade gracefully to no-tool mode

## Open Questions

- What is the exact CDK property name for attaching an HTTP backend URL to an AgentCore Gateway tool? (needs verification against `aws-cdk-lib` `BedrockAgentCore` L1 constructs or `CfnResource` raw properties)
- Does `amazon_bedrock_agentcore.tools.MCPToolset` support a `discovery_query` parameter, or does semantic discovery work through a custom MCP `tools/search` call? (needs SDK version check)
