## Context

GridWise is a FastAPI + MongoDB service (Beanie ODM) with a React/Vite frontend. It currently manages F1 Fantasy teams, validates them against a configurable rule engine, and tracks transfer history. An existing `service/app/agent/` directory contains a Bedrock Agents architecture (CDK Lambda-per-action-group + OpenAPI schemas on S3) that was designed but never deployed.

This change replaces that architecture entirely and integrates an AI advisor directly into the FastAPI service using Google ADK as the agentic framework and AWS AgentCore for managed memory and gateway infrastructure.

## Goals / Non-Goals

**Goals:**
- Ship a working conversational AI advisor reachable via a chat page
- Embed the agent in the existing FastAPI process — no new services to deploy
- Reuse existing `RuleEngine` and `TeamService` logic directly from agent tools via AgentCore Gateway
- Parallel data gathering across F1 data, external intelligence, and user fantasy context
- Long-term memory per user (preferences, chip history, past recommendations) — read at session start, written after recommendation is accepted
- Auth from zero: Cognito user pool → JWT → `user_id` injected into all agent calls via ADK session state

**Non-Goals:**
- Training or using an ML model (Claude reasons directly over raw data)
- Deploying the original CDK Lambda stack
- Team page button and creation panel UX (follow-on, not MVP)
- Multi-user leaderboards or social features

## Decisions

### 1. Google ADK over AWS Bedrock Agents (console-configured)

Bedrock Agents requires OpenAPI schemas uploaded to S3, Lambda functions per action group, and manual console wiring. ADK is code-first: agents, tools, and orchestration are Python classes. This means the full agent graph is version-controlled, testable locally, and refactorable without AWS console operations.

*Alternative considered*: Keep the existing Bedrock Agents approach and write the 5 missing Lambda handlers. Rejected because the CDK stack is operationally heavier for what is effectively a Python service.

### 2. Claude via Bedrock + LiteLLM bridge — Sonnet for root, Haiku for sub-agents

Staying in the AWS ecosystem lets AgentCore IAM roles authenticate to Bedrock without managing a separate Anthropic API key. LiteLLM provides model strings as a drop-in for ADK's `LiteLlm` model class.

- **Root `F1FantasyAdvisor`**: `bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0` — multi-source synthesis requires strong reasoning
- **Sub-agents** (`F1DataAgent`, `IntelAgent`, `FantasyContextAgent`, `SubmissionAgent`): `bedrock/anthropic.claude-3-haiku-20240307-v1:0` — mechanical data-fetching and tool-calling tasks don't require heavy reasoning; Haiku reduces cost and latency per query

*Alternative considered*: All agents use Sonnet. Rejected — sub-agents have narrow, mechanical jobs that Haiku handles well, and running Sonnet for all 5 agents per query is unnecessarily expensive.

*Alternative considered*: Claude via Anthropic API directly. Simpler setup but splits infrastructure across two cloud providers and requires an additional secret.

*Alternative considered*: Gemini (native ADK model). Zero adapter needed, but Claude's reasoning quality on structured data analysis is better suited for the multi-source synthesis this advisor requires.

### 3. Agent embedded in FastAPI (not a separate service)

The ADK Runner runs within the GridWise FastAPI process. Tools access GridWise data through AgentCore Gateway (see Decision 6). A separate agent service would add a deployment dependency.

*Risk*: Agent inference (CPU/memory) competes with API request handling in the same process. Mitigated by FastAPI's async model — LLM calls are I/O-bound and yield the event loop.

### 4. ParallelAgent for data gathering — all three sub-agents write to short-term memory

Three data-gathering sub-agents (`F1DataAgent`, `IntelAgent`, `FantasyContextAgent`) run concurrently under a `ParallelAgent`. Each sub-agent writes its results to AgentCore short-term memory keyed by `session_id` after its tools complete. The root agent reads all three results from short-term memory after `DataGathering` finishes before synthesizing a recommendation.

Separation of concerns is explicit: F1 performance data, external market/sentiment intelligence, and user fantasy state are independent domains, each owned by one agent with a narrow tool set. Sequential execution would add 2–5 seconds of unnecessary latency.

### 5. SubmissionAgent isolated for write operations

Only `SubmissionAgent` has write-capable tools (`validate_team`, `submit_team`). The three parallel data agents are read-only. This makes the write boundary explicit in the agent graph and prevents accidental team mutations during data gathering.

### 6. One AgentCore Gateway — hosts all tools (external and internal)

A single AgentCore Gateway resource hosts all 10 tools: external API tools (`get_live_session_data`, `get_historical_performance`, `get_weather`, `get_odds`, `get_reddit_sentiment`) and internal GridWise tools (`get_user_team`, `get_current_prices`, `get_available_chips`, `validate_team`, `submit_team`).

All sub-agents connect to the Gateway and receive ADK-compatible `MCPToolset` objects. This unifies IAM, connection management, and observability under a single resource.

*Alternative considered*: Internal DB tools as plain Python ADK functions (no gateway). Rejected in favor of a uniform tool hosting layer — all tools registered and observable in one place, with consistent IAM and retry behavior.

### 7. user_id injected server-side via ADK session state

`user_id` (Cognito `sub` claim) is extracted from the validated JWT in FastAPI middleware and injected into the ADK session state before the Runner is invoked. Tools read `user_id` from session context directly — it is never passed as an LLM argument.

This is a security boundary: the LLM must not be the source of `user_id` for data-scoping decisions, as it could be manipulated via prompt injection.

### 8. All sub-agents write results to AgentCore short-term memory

After all tools complete, each parallel sub-agent writes its gathered results to AgentCore short-term memory keyed by `session_id`:
- `F1DataAgent` writes live session data and historical performance
- `IntelAgent` writes weather, odds, and Reddit sentiment
- `FantasyContextAgent` writes current team, prices, and chip status

The root agent reads all three keys from short-term memory after `DataGathering` completes. This prevents re-triggering data gathering for follow-up questions within the same session.

### 9. Long-term memory written post-session after recommendation accepted

Long-term memory (preferences, chip history, past recommendations) is read by the root agent at session start. It is written via a post-session hook triggered when the user accepts a recommendation (i.e., after `SubmissionAgent` successfully calls `submit_team`).

The hook persists: accepted picks (drivers, constructors, DRS Boost), chips used, and any stated preferences captured during the conversation.

*Note*: Long-term memory is read-only for sessions where no recommendation is accepted. The root agent may read an empty store for new users.

### 10. AWS Cognito for auth — covers all routes

Cognito integrates natively with the AWS stack (AgentCore IAM, Bedrock IAM). JWT tokens from Cognito are validated in a FastAPI middleware using `python-jose`. The `user_id` (Cognito sub claim) flows into every agent session and tool call via ADK session state (see Decision 7).

Auth is applied to **all** API routes — `/api/v1/agent/`, `/api/v1/teams/`, `/api/v1/drivers/`, `/api/v1/constructors/`, and `/api/v1/rules/`. Existing routes are not exempt: `FantasyTeam` records are scoped by `user_id`, so unauthenticated access to team routes would allow cross-user data access.

*Alternative considered*: Custom JWT with a symmetric key. Simpler but doesn't buy the managed user lifecycle, password reset, and future MFA that Cognito provides.

### 11. AG-UI protocol + CopilotKit for frontend

The ADK agent exposes an AG-UI compatible endpoint. The React frontend uses CopilotKit to consume it. This replaces a custom SSE implementation with a protocol-native streaming layer.

Key benefits:
- **Generative UI**: `useRenderToolCall` renders `TeamRecommendationCard` when the agent calls `display_team_recommendation` — no JSON parsing of text streams
- **Human-in-the-Loop**: CopilotKit's interrupt pattern handles the confirmation-before-submission flow natively; the agent pauses and waits for an explicit frontend confirmation before delegating to `SubmissionAgent`
- **Shared state**: Agent and frontend share session state bidirectionally

The `display_team_recommendation` tool is a frontend-only tool — the agent calls it to signal that a structured recommendation is ready; CopilotKit renders the card inline in the chat thread.

### 12. SSE for streaming chat responses

ADK's `Runner` supports async streaming via the AG-UI protocol. FastAPI serves the AG-UI endpoint with `StreamingResponse`. CopilotKit on the frontend consumes the stream. This avoids WebSocket complexity for what is a predominantly unidirectional stream.

### 13. All AWS infrastructure provisioned via CDK — zero manual console operations

Every AWS resource (Cognito user pool, AgentCore Gateway, AgentCore Memory store, Secrets Manager entries, IAM roles and policies) is defined in a CDK stack at `service/infra/gridwise-agent-stack.ts`. No resource is created or modified through the AWS console.

The CDK stack creates Secrets Manager entries with **placeholder values only**. Actual API key values are populated locally by the developer running `scripts/populate-secrets.sh`, which reads from a gitignored `secrets.local.env` file and calls `aws secretsmanager put-secret-value`. The actual key values never touch git.

**CRITICAL — API Key Security:**
- API keys (WeatherAPI, Odds API, Reddit credentials, F1 account credentials) MUST NOT be committed to GitHub under any circumstances
- Secrets Manager secrets are created by CDK with dummy placeholder values (`REPLACE_ME`)
- `secrets.local.env` (the file holding real values) is listed in `.gitignore` and must never be staged or committed
- `secrets.local.env.example` (committed) shows the required variable names with placeholder values so developers know what to populate
- `scripts/populate-secrets.sh` reads from `secrets.local.env` and pushes values to Secrets Manager — the script itself contains no key values
- Pre-commit hook verifies no `gridwise/*` secret values are present in staged files

### 14. F1 Fantasy API for live prices, user team, and chip status

The official F1 Fantasy API (`fantasy-api.formula1.com/partner_games/f1`) exposes live driver/constructor prices, the user's actual picked team, and chip (booster) availability. These are called by `FantasyContextAgent` via a new `tools/f1_fantasy.py` module instead of querying GridWise MongoDB.

**Auth flow**: `POST https://api.formula1.com/v2/account/subscriber/authenticate/by-password` with the user's F1 account credentials (stored in Secrets Manager as `gridwise/f1-credentials`). Returns a `SessionId` token used as a cookie/bearer on subsequent Fantasy API calls. The session token is cached in ADK short-term memory for the duration of the session to avoid re-authenticating on every tool call.

**Public endpoints (no auth needed)**:
- `GET /players` — all drivers with live prices; uses API key header `fCUCjWrKPu9ylJwRAv8BpGLEgiAuThx7`
- `GET /teams` — all constructors with live prices

**Authenticated endpoints**:
- `GET /picked_teams?my_current_picked_teams=true` — user's current fantasy team
- `GET /boosters` — chip availability

The API key is a static partner key (`fCUCjWrKPu9ylJwRAv8BpGLEgiAuThx7`) included as a query/header parameter on all requests — stored in code as a constant (it is a public partner key, not a user secret).

*Alternative considered*: Seed driver/constructor prices manually into GridWise MongoDB, updated each race week. Rejected — manual maintenance is error-prone and prices would be stale mid-week when they change.

*Alternative considered*: Scrape the F1 Fantasy website. Rejected — violates ToS and is fragile.

## Risks / Trade-offs

- **ADK + AgentCore SDK maturity** → Both are relatively new. API surfaces may change. Mitigate by pinning dependency versions and isolating AgentCore calls behind the `memory.py` and `gateway.py` adapter modules.
- **LiteLLM Bedrock bridge latency** → Adds ~50ms overhead vs. direct Anthropic API. Acceptable given LLM inference dominates total latency.
- **Parallel external API rate limits** → Three sub-agents fire simultaneously. OpenF1, Reddit, and Odds API all have rate limits. Mitigate with per-tool retry logic and exponential backoff; add circuit breakers in a follow-on.
- **F1 Fantasy API unofficial status** → `fantasy-api.formula1.com` is undocumented/unofficial; F1 may change endpoints or auth without notice. Mitigate by isolating all calls in `tools/f1_fantasy.py` — a single file to update if the API changes. Treat as a best-effort data source; if auth fails, `FantasyContextAgent` should return a structured error and the root agent proceeds with reduced context.
- **F1 account credential security** → F1 username/password stored in Secrets Manager (`gridwise/f1-credentials`). These are the user's personal F1 account — must never be logged, returned in API responses, or passed as LLM arguments.
- **Agent in-process resource contention** → Heavy parallel inference could slow API endpoints. Monitor with CloudWatch; if it becomes a problem, move the agent to a dedicated worker process behind an internal queue.
- **Root agent delegation unpredictability** → Claude decides dynamically when to call `DataGathering`. Aggressive system prompt constraints and explicit tool descriptions mitigate wrong delegation, but integration tests should cover the happy path end-to-end.
- **CopilotKit dependency** → Adds a third-party frontend dependency. Mitigated by the AG-UI protocol being open — CopilotKit can be swapped for another AG-UI client without changing the backend.

## Migration Plan

1. Delete `service/app/agent/schemas/`, `service/app/agent/lambda/`, and `service/app/agent/infra/` — no deployed resources to tear down (CDK stack was never deployed)
2. Create CDK stack at `service/infra/gridwise-agent-stack.ts` for all new AWS resources
3. Run `cdk deploy` — creates Cognito user pool, AgentCore Gateway, AgentCore Memory store, IAM roles, and Secrets Manager entries with placeholder values
4. Run `scripts/populate-secrets.sh` locally to push real API key values into Secrets Manager
5. Create new `service/app/agent/` structure (`agents.py`, `memory.py`, `gateway.py`, `tools/`)
6. Add new dependencies to `requirements.txt` and frontend `package.json`
7. Add auth middleware to FastAPI — applied to all routes including existing ones
8. Register agent router under `/api/v1/agent`
9. Deploy updated FastAPI service
10. Ship chat page frontend with CopilotKit

**Rollback**: Agent router and auth middleware can be disabled via feature flag env var. `cdk destroy` tears down the agent infrastructure without affecting the FastAPI service itself.

## Open Questions

- AgentCore Gateway tool registration format — does it accept MCP tool definitions directly from ADK, or does it require a separate registration step? Need to verify against current AgentCore SDK docs at implementation time.
