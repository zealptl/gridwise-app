<!-- ============================================================
  SECURITY — READ BEFORE IMPLEMENTING
  API keys (WeatherAPI, Odds API, Reddit, F1 account credentials) MUST NOT be committed
  to GitHub. Real values live in secrets.local.env (gitignored) and are pushed to
  Secrets Manager via scripts/populate-secrets.sh — never via code or commits.
  ============================================================ -->

## 0. CDK Stack Split

- [x] 0.1 Create `service/infra/gridwise-foundation-stack.ts` — move IAM roles (`gridwise-fastapi-service-role`, `gridwise-gateway-service-role`), Cognito user pool + client, and Secrets Manager secrets out of `gridwise-agent-stack.ts` into this new stack; write Cognito IDs to SSM (`/gridwise/cognito/user-pool-id`, `/gridwise/cognito/app-client-id`); export IAM role ARNs as `CfnOutput`
- [x] 0.2 Add `gridwise-agent-runtime-role` IAM role to `gridwise-foundation-stack.ts` — trust principal `bedrock-agentcore.amazonaws.com`; grant: `bedrock:InvokeModel` + `InvokeModelWithResponseStream` on Claude model ARNs, `bedrock-agentcore:CreateEvent`, `ListEvents`, `GetMemory`, `RetrieveMemories`, `GetLastKTurns` on `memory/*`, `bedrock-agentcore:InvokeGateway` + `GetGateway` + `ListGatewayTargets` on `*`, `secretsmanager:GetSecretValue` on `gridwise/*`, `ssm:GetParameter` + `GetParameters` on `gridwise/*`; export ARN as `CfnOutput` and write to SSM `/gridwise/iam/agent-runtime-role-arn`
- [x] 0.3 Rename existing `gridwise-agent-stack.ts` resources to `gridwise-agent-stack.ts` (keep filename); import IAM role ARNs from Foundation stack via `Fn.importValue`; remove resources now in Foundation stack
- [x] 0.4 Register both stacks in `service/infra/bin/app.ts` (or equivalent CDK entrypoint); verify `cdk ls` shows `GridwiseFoundationStack` and `GridwiseAgentStack`
- [x] 0.5 Fix IAM memory permissions on `gridwise-fastapi-service-role` in Foundation stack — replace `PutMemoryRecord`, `SearchMemory`, `DeleteMemoryRecord` with `CreateEvent`, `ListEvents`, `GetMemory`, `RetrieveMemories`, `GetLastKTurns` on `arn:aws:bedrock-agentcore:*:${account}:memory/*`

## 1. CDK Stack 1 Deploy — Foundation

- [x] 1.1 Run `cd service/infra && cdk deploy GridwiseFoundationStack` — verify exit code 0; confirm outputs: `UserPoolId`, `UserPoolClientId`, `FastApiRoleArn`, `GatewayServiceRoleArn`
- [x] 1.2 Confirm SSM params written: `/gridwise/cognito/user-pool-id`, `/gridwise/cognito/app-client-id`, `/gridwise/iam/fastapi-role-arn`

## 2. Cognito Tier Attribute

- [x] 2.1 Add `custom:tier` custom attribute (string, mutable) to the Cognito user pool in `gridwise-foundation-stack.ts`
- [x] 2.2 Update `/auth/register` endpoint in `service/app/routers/auth.py` to call `AdminUpdateUserAttributes` setting `custom:tier = "free"` after user creation
- [x] 2.3 Add `get_user_tier(jwt_token: str) -> str` to `service/app/auth.py` — decodes JWT, returns `custom:tier` claim, defaults to `"free"` if absent

## 3. Docker Images

- [x] 3.1 Create `service/Dockerfile` for the FastAPI service — base `python:3.12-slim`, install `uv`, copy `service/` (excluding `infra/`), run `uv sync --frozen`, entrypoint `uvicorn app.main:app --host 0.0.0.0 --port 8080`
- [x] 3.2 Create `service/agent.Dockerfile` for the AgentCore Runtime — same base; entrypoint calls `python runtime_entry.py` (the F1 agent `BedrockAgentCoreApp` entrypoint written in task 10)
- [x] 3.3 Create ECR repository `gridwise-fastapi` and `gridwise-agent-runtime` via CDK in `gridwise-agent-stack.ts` (or `aws ecr create-repository` if doing manually); build and push both images: `docker build -f service/Dockerfile -t gridwise-fastapi .` + `docker tag ... && docker push`

## 4. FastAPI Tool Endpoints

- [x] 4.1 Create `service/app/routers/agent_tools.py` with IAM SigV4 auth middleware that verifies all `/api/v1/agent/tools/*` requests are signed by `gridwise-fastapi-service-role`
- [x] 4.2 Add `POST /agent/tools/get-live-session-data` — calls `get_live_session_data()` from `tools/f1_data.py`
- [x] 4.3 Add `POST /agent/tools/get-historical-performance` — calls `get_historical_performance()` from `tools/f1_data.py`
- [x] 4.4 Add `POST /agent/tools/get-weather` — calls `get_weather(circuit_location)` from `tools/intelligence.py`
- [x] 4.5 Add `POST /agent/tools/get-odds` — calls `get_odds()` from `tools/intelligence.py`
- [x] 4.6 Add `POST /agent/tools/get-reddit-sentiment` — calls `get_reddit_sentiment(race_name)` from `tools/intelligence.py`
- [x] 4.7 Add `POST /agent/tools/get-user-team` — calls `get_user_team(session_state)` from `tools/fantasy.py`
- [x] 4.8 Add `POST /agent/tools/get-current-prices` — calls `get_current_prices()` from `tools/fantasy.py`
- [x] 4.9 Add `POST /agent/tools/get-available-chips` — calls `get_available_chips(session_state)` from `tools/fantasy.py`
- [x] 4.10 Add `POST /agent/tools/get-active-rules` — calls `get_active_rules()` from `tools/fantasy.py`
- [x] 4.11 Add `POST /agent/tools/validate-team` — calls `validate_team(team, user_team_count)` from `tools/submission.py`
- [x] 4.12 Add `POST /agent/tools/submit-team` — enforces `validated: true` in request body (HTTP 422 if absent/false) before calling `submit_team(session_state, team)`
- [x] 4.13 Register `agent_tools` router in `service/app/main.py` under `/api/v1/agent/tools` prefix

## 5. Lambda Proxy — SigV4 Signing Fix

- [x] 5.1 Replace the inline Lambda handler in `gridwise-agent-stack.ts` with a `lambda.Code.fromAsset(...)` pointing at `service/app/agent/lambda/tools_proxy/` — move handler code out of the CDK TypeScript string
- [x] 5.2 Rewrite the handler to sign each outbound HTTP request using `botocore` SigV4: use `botocore.auth.SigV4Auth` + `botocore.awsrequest.AWSRequest`, sign with the Lambda execution role's credentials (`botocore.session.Session().get_credentials()`), attach signed headers to the `urllib` request before forwarding to FastAPI

## 6. AgentCore Memory Resources

- [x] 6.1 Write `scripts/create_memory_resources.py` now (before checking CDK): use `bedrock_agentcore.memory.MemoryClient` to create session store (no strategies, 30-day expiry) and long-term store (USER_PREFERENCE + SEMANTIC, 90-day expiry); write both IDs to SSM (`/gridwise/agentcore/session-memory-id`, `/gridwise/agentcore/memory-id`) and print them; script should be idempotent (check if resources exist before creating)
- [x] 6.2 Run `cdk synth GridwiseAgentStack` — inspect the synthesized CloudFormation template; confirm whether `agentcore.Memory` L2 construct is available in the installed `aws-cdk-lib` version
- [x] **If CDK construct available** — 6.3a: Add `agentcore.Memory` session store to `gridwise-agent-stack.ts` (`memoryName: "gridwise-session-store"`, `expirationDuration: cdk.Duration.days(30)`, no strategies); add `agentcore.Memory` long-term store (`memoryName: "gridwise-memory"`, `expirationDuration: cdk.Duration.days(90)`, `memoryStrategies: [usingBuiltInUserPreference(), usingBuiltInSemantic()]`); write both IDs to SSM and `CfnOutput`
- [x] **If CDK construct unavailable** — 6.3b: Run `scripts/create_memory_resources.py`; confirm both IDs written to SSM before proceeding to Stack 2 deploy
- [x] 6.4 Add `CfnOutput` (or script log) for `SessionMemoryId` and `LongTermMemoryId`

## 7. bedrock-agentcore Package

- [x] 7.1 Add `bedrock-agentcore = ">=1.8.0"` to `service/pyproject.toml` dependencies
- [x] 7.2 Run `uv sync` in `service/` and verify `from bedrock_agentcore.memory import MemoryClient` imports successfully

## 8. memory.py Rewrite

- [x] 8.1 Delete the current `service/app/agent/memory.py` content entirely (it uses fictional boto3 method names)
- [x] 8.2 Rewrite `service/app/agent/memory.py` implementing `google.adk.memory.base_memory_service.BaseMemoryService` with class `AgentCoreMemoryService`:
  - Constructor: reads memory ID from `AGENTCORE_MEMORY_ID` env var or `/gridwise/agentcore/memory-id` SSM fallback; lazily initializes `MemoryClient(region_name=...)` on first use
  - `search_memory(app_name, user_id, query)`: calls `client.get_last_k_turns(memory_id, actor_id=user_id, session_id=app_name, k=5)` then `client.retrieve_memories(memory_id, namespace=<substituted>, query=query, top_k=5)` per strategy; returns `SearchMemoryResponse` with combined `MemoryEntry` objects
  - `add_session_to_memory(session)`: collects text events; calls `client.create_event(memory_id, actor_id=session.user_id, session_id=session.id, messages=[...])` in one batch; skips if no text events
  - `actor_id` is always the Cognito `sub` claim
- [x] 8.3 Remove the `_fallback_cache` in-process dict
- [x] 8.4 Export `AgentCoreMemoryService` from `service/app/agent/memory.py`

## 9. session.py — New File

- [x] 9.1 Create `service/app/agent/session.py` implementing `google.adk.sessions.base_session_service.BaseSessionService` with class `AgentCoreSessionService`:
  - Constructor: reads session store ID from `AGENTCORE_SESSION_MEMORY_ID` env var or `/gridwise/agentcore/session-memory-id` SSM fallback; initializes `MemoryClient`; maintains `_pending_sessions` dict
  - `create_session(app_name, user_id, state, session_id)`: mints `Session`; if seed state exists writes init event; stores in `_pending_sessions`
  - `get_session(app_name, user_id, session_id, config)`: calls `client.list_events(memory_id, actor_id=user_id, session_id=f"{app_name}__{session_id}", include_payload=True)`; deserializes via `Event.model_validate_json()`; replays `state_delta`s; falls back to `_pending_sessions` if no events
  - `list_sessions`, `delete_session`, `append_event` — implement per design doc §Decision 4
- [x] 9.2 Export `get_session_service()` factory from `session.py`

## 10. AgentCore Runtime — F1 Agent Entrypoint

- [x] 10.1 Create `service/runtime_entry.py` — `BedrockAgentCoreApp` entrypoint for the F1 Advisor agent (mirrors `aws-agentcore/runtime/runtime_entry.py` pattern):
  - Import `BedrockAgentCoreApp` from `bedrock_agentcore.runtime`
  - Wire `AgentCoreSessionService` + `AgentCoreMemoryService` into `Runner`
  - `@app.entrypoint async def handler(payload)` — accepts `{"prompt": str, "user_jwt": str, "user_id": str, "session_id": str?}`; calls `runner.run_async(...)`; returns final text
  - Agent graph (`build_f1_advisor_graph`) refactored to accept `user_jwt` and `user_id` and return the root agent + runner (not the FastAPI-coupled version)
- [x] 10.2 Add `preload_memory` from `google.adk.tools` to the root advisor agent's `tools` list
- [x] 10.3 Add `after_agent_callback` to root agent — persists session and triggers async LTM extraction via `callback_context.add_session_to_memory()`
- [x] 10.4 Update `ADVISOR_SYSTEM_PROMPT` to include `<PAST_CONVERSATIONS>` usage section; describe free vs premium tool availability

## 11. CDK Stack 2 — AgentCore Runtime Custom Resource

- [x] 11.1 Add CDK custom resource in `gridwise-agent-stack.ts` using `cr.Provider` + Lambda-backed handler that calls the `bedrock-agentcore` SDK to create (or update) the AgentCore Runtime pointing at the ECR image pushed in task 3.3
- [x] 11.2 Custom resource handler reads the ECR image URI from a CDK parameter or environment variable; writes the Runtime invocation endpoint to SSM: `/gridwise/agentcore/runtime-endpoint`
- [x] 11.3 Add `CfnOutput` for the AgentCore Runtime endpoint URL

## 12. CDK Stack 2 — App Runner

- [x] 12.1 Add `apprunner.Service` construct to `gridwise-agent-stack.ts` pointing at the `gridwise-fastapi` ECR image; set instance role to `gridwise-fastapi-service-role`; set environment variables: `AWS_REGION`, `ENVIRONMENT=production`; configure health check path `/health`
- [x] 12.2 Pass the App Runner service URL directly to the Lambda proxy `FASTAPI_BASE_URL` environment variable via CDK cross-resource reference (`appRunnerService.serviceUrl`) — removes the need for any SSM pre-seed step; also write it to SSM `/gridwise/service/fastapi-base-url` as a `StringParameter` for other consumers
- [x] 12.3 Add `CfnOutput` for the App Runner URL

## 13. CDK Stack 2 Deploy

- [x] 13.1 Run `cd service/infra && cdk deploy GridwiseAgentStack` — verify exit code 0 and all outputs present: `AppRunnerUrl`, `AgentCoreRuntimeEndpoint`, `AgentCoreGatewayId`, `AgentCoreGatewayUrl`, `SessionMemoryId` (if CDK Memory available), `LongTermMemoryId` (if CDK Memory available)
- [x] 13.2 Verify all 11 tools listed: `aws bedrock-agentcore list-gateway-tools --gateway-id <AgentCoreGatewayId>`
- [x] 13.3 Confirm all SSM params written (see SSM Parameters table in design.md)

## 14. Secret Population

- [x] 14.1 Copy `secrets.local.env.example` → `secrets.local.env`; populate with real values: `WEATHER_API_KEY`, `ODDS_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `F1_USERNAME`, `F1_PASSWORD`
- [x] 14.2 Run `scripts/populate-secrets.sh` — verify each of the 4 secrets updated: `aws secretsmanager get-secret-value --secret-id gridwise/weather-api-key` (repeat for each)

## 15. gateway.py — Semantic Discovery Rewrite

- [x] 15.1 Update `AgentCoreGateway.__init__` to accept `jwt: str | None = None` and store it
- [x] 15.2 Rewrite `get_toolset_for_agent` to use `discovery_query` (sub-agent description) and inject `Authorization: Bearer <jwt>` as header on the `MCPToolset` connection; return empty toolset if `jwt` is `None`
- [x] 15.3 Remove `TOOL_REGISTRY` dict and `get_toolset` convenience wrapper
- [x] 15.4 Update `verify_gateway_connection` to test with a sample semantic query and log tool count returned

## 16. agents.py — Runner Wiring + JWT Propagation

- [x] 16.1 Update `build_f1_advisor_graph()` to accept `user_jwt: str | None` and `user_id: str` parameters
- [x] 16.2 Wire `AgentCoreSessionService` + `AgentCoreMemoryService` into the `Runner` (used by the AgentCore Runtime entrypoint in `runtime_entry.py`)
- [x] 16.3 Pass `user_jwt` to `AgentCoreGateway(jwt=user_jwt)` and `user_id` for session creation
- [x] 16.4 Rewrite `_build_f1_data_agent` — remove `tool_names`; pass description as `discovery_query`; enrich instruction with failure handling for `available: false` responses
- [x] 16.5 Rewrite `_build_intel_agent` — remove `tool_names`; pass description as `discovery_query`; add free-tier empty toolset handling
- [x] 16.6 Rewrite `_build_fantasy_context_agent` — remove `tool_names`; enrich instruction with required sub-fields and null handling
- [x] 16.7 Rewrite `_build_submission_agent` — remove `tool_names`; enforce validate-before-submit in instruction

## 17. Chat Endpoint — Runtime Invocation

- [x] 17.1 Update the chat endpoint in `service/app/routers/agent.py` to extract the raw JWT string from `Authorization: Bearer` header
- [x] 17.2 Decode JWT (without verification — Cognito middleware already verified) to extract `sub` claim as `user_id`
- [x] 17.3 Replace direct call to `build_f1_advisor_graph()` with SigV4-signed invocation of the AgentCore Runtime endpoint (read from SSM `/gridwise/agentcore/runtime-endpoint`); pass `{"prompt": message, "user_jwt": token, "user_id": sub, "session_id": session_id}` as payload
- [x] 17.4 Return HTTP 401 if `Authorization` header is absent or `sub` claim cannot be extracted
- [x] 17.5 Stream the Runtime response back to the frontend (or collect and return if Runtime doesn't support streaming)

## 18. Frontend — Apply Recommendation Interrupt

- [x] 18.1 Add "Apply Recommendation" button to `TeamRecommendationCard` component; wire it to resolve the active CopilotKit Human-in-the-Loop interrupt with a confirmation payload
- [x] 18.2 Disable the button when no interrupt is pending; disable immediately after click to prevent double-submission
- [x] 18.3 Display submission outcome in the chat thread: success message with team ID on success, violation list on validation failure

## 19. Verification

- [ ] 19.1 Test with a free-tier user JWT: confirm only 8 tools returned by semantic discovery (intelligence tools absent)
- [ ] 19.2 Test with a premium-tier user JWT: confirm all 11 tools returned
- [ ] 19.3 End-to-end test: register → login → open advisor → send recommendation request → all parallel sub-agents fire → root agent streams response with `TeamRecommendationCard` rendered
- [ ] 19.4 Test Apply Recommendation: click button → interrupt resolved → `SubmissionAgent` validates → submits → success message in chat
- [ ] 19.5 Test unauthenticated chat request returns HTTP 401
- [ ] 19.6 Test session durability: send a chat message, restart the AgentCore Runtime container, send follow-up — agent recalls prior turn from `AgentCoreSessionService`
- [ ] 19.7 Test long-term memory: complete two sessions as the same user; third session `<PAST_CONVERSATIONS>` block contains extracted preferences (~90s extraction delay)
- [ ] 19.8 Test actor isolation: two users' memories never appear in each other's `<PAST_CONVERSATIONS>` blocks
- [ ] 19.9 Test partial failure: mock OpenF1 unavailable → agent acknowledges missing data and returns reduced-confidence recommendation
- [ ] 19.10 Test Lambda → FastAPI SigV4: confirm tool endpoint returns 403 when called without a signed request
