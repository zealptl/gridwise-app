## Context

The F1 Fantasy Advisor is fully implemented in code — ADK agent graph, sub-agents, tool implementations, and the FastAPI chat endpoint are all in place. Five things block it from working end-to-end:

1. **No AgentCore Memory resources**: IAM permissions reference memory operations but no Memory resources were ever created. `memory.py` uses fictional boto3 method names (`store_memory`, `retrieve_memories`) on a service that doesn't exist as a boto3 client. Every memory call silently falls back to an in-process dict.
2. **No FastAPI tool routes**: The CDK Lambda proxy routes AgentCore Gateway calls to `POST /api/v1/agent/tools/<tool-name>`, but these endpoints don't exist. Tool calls 404.
3. **CDK stack never deployed**: Gateway, Cognito, Secrets, IAM roles exist only in TypeScript.
4. **gateway.py uses hardcoded tool registry**: Semantic discovery not wired; `custom:tier` missing.
5. **No deployment target for FastAPI or the agent**: The CDK IAM role supports EC2, ECS, and Lambda principals but no compute is provisioned. The ADK Runner has no runtime home.

## Goals / Non-Goals

**Goals:**
- FastAPI deployed to AWS App Runner; agent deployed as a separate AgentCore Runtime container
- CDK split into two stacks: Stack 1 (IAM + Cognito + Secrets), Stack 2 (App Runner + AgentCore Runtime + Lambda proxy + Memory + Gateway)
- Two AgentCore Memory resources: session store (durable event log) and long-term memory (USER_PREFERENCE + SEMANTIC extraction)
- Correct `memory.py` using `bedrock_agentcore.memory.MemoryClient` implementing `BaseMemoryService`
- New `session.py` with `AgentCoreSessionService(BaseSessionService)` backed by session store
- All 11 tools callable end-to-end: AgentCore Gateway → Lambda proxy (SigV4-signed) → FastAPI endpoint → tool implementation
- CDK Stack 1 + Stack 2 fully deployed; secrets populated with real values via `populate-secrets.sh`
- `custom:tier` JWT claim for per-tool tier enforcement at the gateway
- Semantic tool discovery replacing hardcoded tool name lists in `agents.py`
- "Apply Recommendation" CopilotKit interrupt wired on the frontend

**Non-Goals:**
- Per-tool rate limiting
- Gateway canary deployments or blue/green
- Changes to the chat API request/response contract
- New tools beyond the existing 11
- Custom memory extraction prompts (using built-in strategies)

## Architecture

```
User (Cognito JWT)
       │
       ▼
POST /api/v1/agent/chat
  (FastAPI — App Runner)
  extract JWT + sub claim
       │
       ▼ invoke (SigV4)
AgentCore Runtime container
  BedrockAgentCoreApp
  ┌────────────────────────────────────────────────────┐
  │  ADK Runner                                         │
  │  session_service = AgentCoreSessionService          │
  │    └── Memory Resource: session store (no LTM)      │
  │  memory_service  = AgentCoreMemoryService           │
  │    └── Memory Resource: long-term (USER_PREF+SEM)   │
  │                                                     │
  │  root_agent (F1 Advisor)                            │
  │   tools: [preload_memory, ...]                      │
  │   after_agent_callback: persist_session_callback    │
  │   ├── F1DataAgent    → MCPToolset                   │
  │   ├── IntelAgent     → MCPToolset  ─────────────────┼──► AgentCore Gateway
  │   ├── FantasyAgent   → MCPToolset                   │    (MCP endpoint, Cognito JWT)
  │   └── SubmissionAgent → MCPToolset                  │         │
  └────────────────────────────────────────────────────┘         │
                                                                  ▼
                                                         Lambda Proxy
                                                         (gridwise-tools-proxy)
                                                         signs requests with SigV4
                                                                  │
                                                                  ▼
                                                         POST /api/v1/agent/tools/*
                                                         (FastAPI — App Runner)
                                                         SigV4 auth middleware
                                                                  │
                                                                  ▼
                                                         tools/*.py implementations
```

## Decisions

### Decision 1: Two AgentCore Memory resources — CDK first, Python fallback
Attempt to use `agentcore.Memory` CDK L2 construct (same package as the `agentcore.Gateway` construct already deployed). If `agentcore.Memory` does not exist in the installed `aws-cdk-lib` version, fall back to `scripts/create_memory_resources.py` — a one-time Python SDK script using `MemoryClient` that writes resource IDs to SSM. Verify with `cdk synth` before attempting `cdk deploy`.

Resource 1 — session store: no extraction strategies, 30-day expiry. Used exclusively as a durable event log for `AgentCoreSessionService`.

Resource 2 — long-term memory: built-in `USER_PREFERENCE` + `SEMANTIC` strategies, 90-day expiry. Used by `AgentCoreMemoryService` for cross-session context injection via `preload_memory`.

### Decision 2: bedrock-agentcore Python package, not boto3
The correct SDK is `from bedrock_agentcore.memory import MemoryClient` (package: `bedrock-agentcore >= 1.8.0`). There is no `boto3.client("bedrock-agentcore")` — that service name doesn't exist in boto3. The current `memory.py` is entirely incorrect and must be rewritten from scratch.

### Decision 3: actor_id = Cognito sub claim
The `actor_id` parameter in all AgentCore Memory calls (namespacing per-user memories) SHALL be the Cognito JWT `sub` claim — a stable UUID that never changes even if the user updates their email.

### Decision 4: AgentCoreSessionService replaces InMemorySessionService
Each ADK `Event` is JSON-serialized (`event.model_dump_json(by_alias=True, exclude_none=True)`) and stored as a single AgentCore message via `create_event`. On `get_session`, events are reloaded via `list_events` and state is rebuilt by replaying `state_delta`s. Session IDs are encoded as `{app_name}__{session_id}`.

Partial events (`event.partial = True`) are not persisted — only complete events go to AgentCore. An in-process cache holds sessions that have no events yet (between `create_session` and the first `append_event`).

### Decision 5: preload_memory runs before each LLM call automatically
`preload_memory` fires before the model step and injects retrieved memories as `<PAST_CONVERSATIONS>` in the prompt. The model never decides whether to call it.

### Decision 6: CDK split into two stacks to break circular dependency
Stack 1 (`GridwiseFoundationStack`): IAM roles + Cognito + Secrets Manager. Deploy first.
Stack 2 (`GridwiseAgentStack`): App Runner + AgentCore Runtime + Lambda proxy + Memory resources + AgentCore Gateway. Deploy after FastAPI container image is built and pushed to ECR and after `/gridwise/service/fastapi-base-url` SSM param is set.

This eliminates the chicken-and-egg problem: FastAPI needs the IAM role to access SSM/Secrets (Stack 1), and CDK Stack 2 needs the FastAPI URL to configure the Lambda proxy.

### Decision 7: FastAPI deployed to AWS App Runner
App Runner handles TLS, scaling, and routing with minimal CDK config. The `service/` directory gets a `Dockerfile`. The App Runner service uses the `gridwise-fastapi-service-role` (created in Stack 1) as its instance role. Stack 2 provisions the App Runner service pointing at the ECR image. The App Runner service URL is passed directly to the Lambda proxy `FASTAPI_BASE_URL` env var via CDK cross-resource reference — no SSM pre-seed step required.

### Decision 8: ADK agent runs as AgentCore Runtime (separate container)
The F1 Advisor agent graph is extracted from FastAPI into a `BedrockAgentCoreApp` container (pattern from `aws-agentcore/runtime/runtime_entry.py`). FastAPI's chat endpoint invokes the AgentCore Runtime via SigV4. The Runtime container uses `gridwise-agent-runtime-role` (created in Stack 1) as its execution role — this role grants Bedrock model invocation, AgentCore Memory + Gateway access, Secrets Manager, and SSM. The Runtime is deployed via CDK Stack 2 as a custom resource that calls the AgentCore SDK to create/update the runtime after pushing the image to ECR.

### Decision 9: Lambda proxy signs requests to FastAPI using SigV4 (botocore)
The inline Lambda handler must sign each outbound HTTP request using `botocore` request signing before forwarding to the FastAPI tool endpoints. FastAPI verifies the SigV4 signature to confirm the caller is `gridwise-fastapi-service-role`.

### Decision 10: Thin endpoint wrappers with no duplicated logic
Each tool endpoint is a one-liner calling the existing `tools/*.py` function. Business logic stays in tool implementations. The router handles SigV4 auth middleware and request deserialization only.

### Decision 11: Semantic discovery replaces TOOL_REGISTRY
`gateway.py` uses the gateway's semantic search with a `discovery_query` (sub-agent description) and injects `Authorization: Bearer <jwt>` as a header. Tier filtering happens server-side at the gateway using the `custom:tier` JWT claim.

### Decision 12: Correct IAM permissions for AgentCore Memory
The CDK currently grants `PutMemoryRecord`, `SearchMemory`, `DeleteMemoryRecord` — these don't match the real `MemoryClient` SDK methods. The correct permissions are `CreateEvent`, `ListEvents`, `GetMemory`, `RetrieveMemories`, `GetLastKTurns`.

## SSM Parameters

| Parameter | Written by | Read by | Notes |
|---|---|---|---|
| `/gridwise/agentcore/session-memory-id` | CDK Stack 2 or fallback script | AgentCore Runtime startup | Session store Memory resource ID |
| `/gridwise/agentcore/memory-id` | CDK Stack 2 or fallback script | AgentCore Runtime startup | Long-term Memory resource ID |
| `/gridwise/agentcore/gateway-endpoint` | CDK Stack 2 | AgentCore Runtime startup | AgentCore Gateway MCP URL |
| `/gridwise/agentcore/runtime-endpoint` | CDK Stack 2 custom resource | FastAPI chat endpoint | AgentCore Runtime invocation URL |
| `/gridwise/cognito/user-pool-id` | CDK Stack 1 | FastAPI auth + Runtime | Cognito user pool |
| `/gridwise/cognito/app-client-id` | CDK Stack 1 | FastAPI auth | Cognito app client |
| `/gridwise/iam/agent-runtime-role-arn` | CDK Stack 1 | CDK Stack 2 custom resource | IAM role for AgentCore Runtime container |
| `/gridwise/service/fastapi-base-url` | CDK Stack 2 (App Runner URL) | Lambda proxy, other consumers | Written by CDK after App Runner provisioned; Lambda reads via cross-resource ref |

## Deploy Order

1. `cdk deploy GridwiseFoundationStack` — creates IAM roles, Cognito, Secrets Manager
2. Build + push FastAPI Docker image to ECR; build + push AgentCore Runtime image to ECR
3. Set SSM param: `aws ssm put-parameter --name /gridwise/service/fastapi-base-url --value <apprunner-url> --type String`
4. **Memory**: Run `cdk synth GridwiseAgentStack` — if `agentcore.Memory` construct is available, proceed to step 5; otherwise run `scripts/create_memory_resources.py` to create resources via SDK and write IDs to SSM, then proceed
5. `cdk deploy GridwiseAgentStack` — creates App Runner service, AgentCore Runtime (custom resource), Lambda proxy, Memory resources (if CDK construct available), AgentCore Gateway
6. Verify CloudFormation outputs: App Runner URL, Runtime endpoint, Cognito IDs, Memory IDs, Gateway ID/URL, Lambda ARN
7. Confirm SSM params written (all 7 parameters in table above)
8. Populate secrets: copy `secrets.local.env.example` → `secrets.local.env`, fill values, run `scripts/populate-secrets.sh`
9. Rewrite `memory.py`, create `session.py`, wire `agents.py` — rebuild + push AgentCore Runtime image; update runtime via CDK or SDK
10. Rewrite `gateway.py` (semantic discovery + JWT) and update chat endpoint — rebuild + push FastAPI image; App Runner picks up new image
11. Implement frontend Apply Recommendation interrupt — deploy frontend
12. Smoke test: free user → 8 tools; premium user → 11 tools; end-to-end chat → recommendation card rendered; second session uses prior memory context

**Rollback**: revert `gateway.py` to stub (empty toolsets) — agents degrade gracefully to no-tool mode. Memory resources persist independently.

## Risks / Trade-offs

- **`agentcore.Memory` CDK L2 construct may not exist** → Mitigation: `cdk synth` check first; Python SDK fallback script (`scripts/create_memory_resources.py`) ready as alternative
- **`memory.py` was using fictional API calls** → Fully resolved by rewrite using `MemoryClient`
- **Long-term extraction is async (~60–90s after session ends)** → `preload_memory` returns empty for new users and enriches gradually
- **AgentCore Runtime custom resource adds CDK complexity** → Use `cr.Provider` + Lambda-backed custom resource; isolate in a construct class
- **Semantic discovery non-determinism** → Sub-agent instructions handle tool unavailability gracefully
- **Two Docker images to maintain** → FastAPI image (`service/Dockerfile`) + Runtime image (`service/agent/Dockerfile`)

## Open Questions

- Does `amazon_bedrock_agentcore.tools.MCPToolset` accept `discovery_query` as a constructor parameter, or is semantic search invoked differently? (needs SDK version check against installed package)
- Does `agentcore.Memory` exist as a CDK L2 construct in the currently installed `aws-cdk-lib` version? (check with `cdk synth` before Stack 2 deploy)
