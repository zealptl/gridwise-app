## Why

The F1 Fantasy Advisor agent graph is implemented but not yet operational end-to-end. Four things block it:

1. **No AgentCore Memory resources**: The CDK stack has IAM permissions for memory operations but no Memory resources were ever created. The current `memory.py` uses fictional boto3 method names that don't exist — all memory calls silently fall back to an in-process dict that is lost on every FastAPI restart.
2. **No FastAPI tool endpoints**: The CDK Lambda proxy (`gridwise-tools-proxy`) routes AgentCore Gateway calls to `POST /api/v1/agent/tools/<tool-name>`, but these endpoints don't exist yet. Tool calls will 404.
3. **CDK stack never deployed**: The AgentCore Gateway, Cognito User Pool, Secrets Manager secrets, and IAM roles exist only in TypeScript — they've never been `cdk deploy`ed.
4. **gateway.py uses hardcoded tool names**: Semantic discovery is not wired; `custom:tier` Cognito attribute for free/premium gating is missing.

## What Changes

- Add two `agentcore.Memory` CDK resources: a session store (no strategies) and a long-term memory store (USER_PREFERENCE + SEMANTIC strategies), both writing their IDs to SSM
- Add `bedrock-agentcore >= 1.8.0` Python package to service dependencies
- Rewrite `memory.py` from scratch using `MemoryClient` from `bedrock_agentcore.memory` implementing `BaseMemoryService`
- Create new `session.py` implementing `AgentCoreSessionService(BaseSessionService)` backed by the session store memory resource
- Wire both services into the ADK `Runner` in `agents.py`; add `preload_memory` tool to root agent; add `after_agent_callback` for session persistence
- Add 11 FastAPI tool endpoints under `/api/v1/agent/tools/*` so the Lambda proxy can forward AgentCore Gateway calls to real tool implementations
- Deploy the CDK stack (`cdk deploy`) to create Cognito, Secrets Manager secrets, IAM roles, the tools-proxy Lambda, both Memory resources, and the AgentCore Gateway with all 11 tool schemas
- Populate Secrets Manager with real API key values via `scripts/populate-secrets.sh`
- Add `custom:tier` custom attribute to Cognito and wire tier into JWT + auth middleware
- Rewrite `gateway.py` to use semantic discovery with JWT injection (remove hardcoded tool name registry)
- Update `agents.py` to pass user JWT and user_id (Cognito sub claim) through to gateway and Runner
- Update the chat endpoint to extract JWT and sub claim, forward both to the agent graph
- Implement the "Apply Recommendation" CopilotKit Human-in-the-Loop button on the frontend

## Capabilities

### New Capabilities

- `agentcore-memory`: Two CDK Memory resources (session store + long-term), `bedrock-agentcore` package, complete rewrite of `memory.py` using real `MemoryClient` API, new `session.py` with `AgentCoreSessionService` — gives the agent durable session storage and cross-session USER_PREFERENCE + SEMANTIC memory
- `agent-runner-wiring`: ADK `Runner` wired with `AgentCoreSessionService` + `AgentCoreMemoryService`; `preload_memory` tool on root agent auto-injects `<PAST_CONVERSATIONS>` before each turn; `after_agent_callback` persists sessions and triggers async extraction
- `agent-tool-endpoints`: 11 FastAPI POST endpoints that expose F1 data, intelligence, fantasy context, and submission tools with IAM SigV4 auth middleware — these are the HTTP backends the AgentCore Gateway Lambda proxy calls
- `agentcore-gateway-deployment`: CDK deploy of the AgentCore Gateway resource, Lambda proxy, IAM roles, Cognito user pool, both Memory resources, and Secrets Manager secrets; includes post-deploy secret population
- `cognito-tier`: `custom:tier` attribute on Cognito users enabling free/premium tool access differentiation at the gateway level
- `semantic-tool-discovery`: `gateway.py` rewired to discover tools via semantic query + JWT header injection; `agents.py` updated to pass JWT and use description-based discovery instead of hardcoded tool name lists
- `advisor-submit-interrupt`: "Apply Recommendation" frontend button wired as a CopilotKit Human-in-the-Loop interrupt that resolves to trigger `SubmissionAgent`

### Modified Capabilities

## Impact

- `service/infra/gridwise-agent-stack.ts` — add two `agentcore.Memory` resources + SSM outputs; add `custom:tier` Cognito attribute; update IAM permissions to match real SDK method names
- `service/pyproject.toml` — add `bedrock-agentcore >= 1.8.0`
- `service/app/agent/memory.py` — complete rewrite using `MemoryClient` + `BaseMemoryService`
- `service/app/agent/session.py` — new file implementing `AgentCoreSessionService(BaseSessionService)`
- `service/app/agent/agents.py` — wire session/memory services into Runner; add `preload_memory` + `after_agent_callback` to root agent; accept `user_jwt` + `user_id` params
- `service/app/routers/agent_tools.py` — new file (11 tool endpoints)
- `service/app/main.py` — register `agent_tools` router
- `service/app/auth.py` — add `get_user_tier()` utility; update `/auth/register` to set `custom:tier = "free"`
- `service/app/agent/gateway.py` — rewrite to use semantic discovery + JWT injection
- `service/app/routers/agent.py` — extract raw JWT + sub claim, pass to `build_f1_advisor_graph()`
- `app/src/` — add Apply Recommendation interrupt button to advisor page
- AWS: Cognito User Pool, Secrets Manager (4 secrets), IAM roles, Lambda, two AgentCore Memory resources, AgentCore Gateway — all created on first `cdk deploy`
