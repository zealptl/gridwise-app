## Why

The F1 Fantasy Advisor agent currently runs with no tools — `MCPToolset` references tool names but no AgentCore Gateway is deployed, no FastAPI endpoints back those tools, and no access control exists. This change establishes the full tool execution path: FastAPI endpoints as the single backend, AgentCore Gateway as the auth/discovery layer with tier-based access control, and semantic tool loading replacing hardcoded per-agent tool lists.

## What Changes

- **New**: FastAPI router `agent_tools.py` with 11 endpoints at `/agent/tools/*` — internal tools call MongoDB/service layer directly, external API tools are proxied through FastAPI
- **New**: AgentCore Gateway provisioned in CDK with all 11 tools registered, each with OpenAPI description and tier-based access policy (`free` | `premium`)
- **New**: Cognito `custom:tier` attribute added to user pool and set at registration (default: `free`)
- **Modified**: `gateway.py` — rewritten to use semantic discovery mode with JWT passthrough instead of empty `MCPToolset(tool_names=[...])` stubs
- **Modified**: `agents.py` — sub-agents drop hardcoded `tool_names`; instructions enriched with detailed reasoning guidance; user JWT flows into agent session context
- **Modified**: Chat API endpoint — extracts `custom:tier` from Cognito JWT and passes it to the agent session

**Tier access policy:**
- Free: `get_live_session_data`, `get_historical_performance`, `get_user_team`, `get_current_prices`, `get_available_chips`, `get_active_rules`, `validate_team`, `submit_team`
- Premium: `get_weather`, `get_odds`, `get_reddit_sentiment`

## Capabilities

### New Capabilities
- `agent-tool-endpoints`: FastAPI HTTP endpoints backing each agent tool; internal tools use existing MongoDB/service layer, external API tools proxy through FastAPI
- `agentcore-gateway-provisioning`: AgentCore Gateway CDK resource with all tools registered — OpenAPI descriptions, tier-based access policies, IAM auth for service-to-service calls
- `gateway-semantic-discovery`: ADK agents discover tools at runtime via semantic search + tier filtering through the gateway; no hardcoded `tool_names` per agent
- `cognito-tier-claim`: Cognito user pool extended with `custom:tier` attribute; JWT carries claim used by gateway access policies and forwarded from chat endpoint to agent

### Modified Capabilities

None — no existing specs to delta against.

## Impact

- `service/app/routers/agent_tools.py` — new file (11 endpoints)
- `service/app/agent/gateway.py` — significant rewrite
- `service/app/agent/agents.py` — tool loading + instruction enrichment
- `service/app/main.py` — register new router; JWT tier extraction at chat endpoint
- `service/app/auth.py` — `custom:tier` claim parsing
- `service/infra/gridwise-agent-stack.ts` — AgentCore Gateway CDK resource + Cognito custom attribute
- No breaking changes to existing chat API contract
