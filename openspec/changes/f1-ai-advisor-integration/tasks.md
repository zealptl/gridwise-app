<!-- ============================================================
  WORKTREE & PR WORKFLOW — READ BEFORE IMPLEMENTING
  Every independent feature section below MUST be developed in its own git worktree.
  Workflow per feature:
    1. Create a dedicated worktree branched from main (e.g. git worktree add ../gridwise-<feature> -b feat/<feature>)
    2. Implement all tasks for that section inside the worktree
    3. Commit all changes with a clear, scoped commit message once development is complete
    4. Open a PR with an appropriate title and description (what, why, notable decisions)
    5. Automerge is permitted as long as there are no merge conflicts — resolve conflicts before merging
  ============================================================ -->

<!-- ============================================================
  SECURITY — READ BEFORE IMPLEMENTING
  API keys (WeatherAPI, Odds API, Reddit, F1 account credentials) MUST NOT be committed
  to GitHub. The CDK stack creates Secrets Manager entries with
  placeholder values only. Real values live in secrets.local.env
  (gitignored) and are pushed to Secrets Manager via
  scripts/populate-secrets.sh — never via code or commits.
  ============================================================ -->

## 1. Cleanup & Dependencies

- [x] 1.1 Remove `service/app/agent/schemas/`, `service/app/agent/lambda/`, and `service/app/agent/infra/` — CDK architecture replaced
- [x] 1.2 Add Python dependencies to `service/requirements.txt`: `google-adk`, `litellm`, `boto3`, `python-jose[cryptography]`, and the AgentCore SDK package
- [x] 1.3 Create new `service/app/agent/` structure: `agents.py`, `memory.py`, `gateway.py`, `tools/__init__.py`, `tools/f1_data.py`, `tools/intelligence.py`, `tools/fantasy.py`, `tools/f1_fantasy.py`, `tools/submission.py`
- [x] 1.4 Add frontend dependencies to `app/package.json`: `@copilotkit/react-core`, `@copilotkit/react-ui`

## 2. Infrastructure as Code (CDK)

- [x] 2.1 Create `service/infra/gridwise-agent-stack.ts` CDK stack — this is the ONLY place AWS resources are created; no console operations permitted
- [x] 2.2 Add to CDK stack: Cognito user pool (email/password auth) + app client; output user pool ID and client ID as CDK `CfnOutput` and SSM parameters
- [x] 2.3 Add to CDK stack: AgentCore Gateway resource; output Gateway endpoint URL as CDK `CfnOutput` and SSM parameter
- [x] 2.4 Add to CDK stack: AgentCore Memory store; output Memory store ID as CDK `CfnOutput` and SSM parameter
- [x] 2.5 Add to CDK stack: Secrets Manager secrets with **placeholder values only** — `gridwise/weather-api-key`, `gridwise/odds-api-key`, `gridwise/reddit-credentials`, `gridwise/f1-credentials` each with value `{"value":"REPLACE_ME"}`
- [x] 2.6 Add to CDK stack: IAM role for the FastAPI service with policies — Bedrock `InvokeModel` (Claude 3.5 Sonnet + Haiku), AgentCore Gateway invoke, AgentCore Memory read/write, Secrets Manager `GetSecretValue` for `gridwise/*`
- [ ] 2.7 Run `cdk bootstrap && cdk deploy` — verify all resources created successfully, capture output SSM parameter names for `.env`

## 3. Local Secret Population (never committed)

- [x] 3.1 Add `secrets.local.env` to `.gitignore` — verify it is ignored before proceeding
- [x] 3.2 Create `secrets.local.env.example` (committed): shows required variable names with `REPLACE_ME` placeholder values — `WEATHER_API_KEY`, `ODDS_API_KEY`, `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `F1_USERNAME`, `F1_PASSWORD`
- [x] 3.3 Create `scripts/populate-secrets.sh` (committed, contains no key values): reads from `secrets.local.env`, calls `aws secretsmanager put-secret-value` for each `gridwise/*` secret (`weather-api-key`, `odds-api-key`, `reddit-credentials`, `f1-credentials`); prints confirmation for each
- [ ] 3.4 Copy `secrets.local.env.example` → `secrets.local.env` locally, populate with real API key values obtained from each provider
- [ ] 3.5 Run `scripts/populate-secrets.sh` — verify each secret is populated in Secrets Manager (check via `aws secretsmanager get-secret-value`)
- [x] 3.6 Add pre-commit hook (`.git/hooks/pre-commit`) that greps staged files for known secret patterns and blocks the commit if found

## 4. Cognito Auth Middleware — All Routes

- [x] 4.1 Implement `service/app/auth.py`: fetch Cognito JWKS from SSM (user pool ID output from CDK), validate JWT signature and claims (`iss`, `aud`, `exp`), extract `user_id` from `sub` claim using `python-jose`
- [x] 4.2 Add FastAPI dependency `get_current_user` that validates the `Authorization: Bearer` header and returns `user_id` — returns HTTP 401 on missing or invalid token
- [x] 4.3 Apply `get_current_user` dependency to **all** routes — `/api/v1/agent/`, `/api/v1/teams/`, `/api/v1/drivers/`, `/api/v1/constructors/`, `/api/v1/rules/`; unauthenticated access to any route returns 401

## 5. AgentCore Gateway Module

- [x] 5.1 Implement `service/app/agent/gateway.py`: connect to AgentCore Gateway using the service IAM role (endpoint URL from SSM, set by CDK), load registered tool definitions, return ADK-compatible `MCPToolset` objects grouped by sub-agent
- [x] 5.2 Register all tool schemas with the AgentCore Gateway (one-time setup, driven by CDK or gateway.py init): `get_live_session_data`, `get_historical_performance`, `get_weather`, `get_odds`, `get_reddit_sentiment`, `get_user_team`, `get_current_prices`, `get_available_chips`, `get_active_rules`, `validate_team`, `submit_team` — note: `get_user_team`, `get_current_prices`, `get_available_chips` now delegate to `tools/f1_fantasy.py` internally; tool names and schemas are unchanged from the gateway's perspective
- [x] 5.3 Verify Gateway connection and tool availability at FastAPI startup (log warning if Gateway unreachable, don't hard-fail startup)

## 6. AgentCore Memory Adapter

- [x] 6.1 Implement `service/app/agent/memory.py`: subclass ADK `BaseMemoryService`, implement `search_memory` (calls AgentCore long-term Memory search API with `user_id` filter) and `add_session_to_memory` (writes session events to AgentCore); Memory store ID read from SSM (set by CDK)
- [x] 6.2 Implement short-term memory write in `memory.py`: `write_session_context(session_id, key, data)` stores sub-agent results keyed by `session_id` + agent key (e.g. `f1_data`, `intel`, `fantasy_context`) with appropriate TTL
- [x] 6.3 Implement short-term memory read in `memory.py`: `read_session_context(session_id, key)` retrieves previously stored sub-agent results, returns `None` if not found
- [x] 6.4 Implement long-term memory write in `memory.py`: `write_recommendation_accepted(user_id, picks, chips_used, preferences)` — called post-session when `submit_team` succeeds; persists accepted team picks, chips used, and stated preferences

## 7. Tool Implementations

- [x] 7.1 Implement `tools/f1_data.py` — `get_live_session_data`: call OpenF1 API (`/sessions`, `/laps`, `/stints`, `/weather`, `/race_control`) for the latest session, return structured dict; handle API unavailability with structured error response
- [x] 7.2 Implement `tools/f1_data.py` — `get_historical_performance`: call Jolpica API for current driver standings, constructor standings, and last-3-race results at the upcoming circuit; handle API unavailability
- [x] 7.3 Implement `tools/intelligence.py` — `get_weather`: call WeatherAPI with circuit location, fetch 3-day forecast; retrieve API key from Secrets Manager (`gridwise/weather-api-key`) — NEVER hardcode the key
- [x] 7.4 Implement `tools/intelligence.py` — `get_odds`: call The Odds API for F1 race winner market, convert odds to implied probabilities; retrieve API key from Secrets Manager (`gridwise/odds-api-key`) — NEVER hardcode the key
- [x] 7.5 Implement `tools/intelligence.py` — `get_reddit_sentiment`: call Reddit OAuth API, fetch recent posts from r/formula1 and r/FantasyF1 mentioning the upcoming race; retrieve credentials from Secrets Manager (`gridwise/reddit-credentials`) — NEVER hardcode credentials
- [x] 7.6 Implement `tools/f1_fantasy.py` — `authenticate_f1_fantasy`: retrieve F1 credentials from Secrets Manager (`gridwise/f1-credentials`), POST to `https://api.formula1.com/v2/account/subscriber/authenticate/by-password` with `DistributionChannel`, `Login`, and `Password`; return `SessionId` token; cache token in ADK session state under key `f1_session_token` to avoid re-auth per tool call — NEVER log or return credentials
- [x] 7.7 Implement `tools/f1_fantasy.py` — `get_f1_fantasy_prices`: call `GET https://fantasy-api.formula1.com/partner_games/f1/players` and `GET /teams` with API key header `fCUCjWrKPu9ylJwRAv8BpGLEgiAuThx7`; return structured list of drivers and constructors with `id`, `name`, `price`, `team`; no auth required for these endpoints
- [x] 7.8 Implement `tools/f1_fantasy.py` — `get_f1_fantasy_team`: call authenticate_f1_fantasy to get session token, then `GET https://fantasy-api.formula1.com/partner_games/f1/picked_teams?my_current_picked_teams=true`; return current team composition, budget remaining, and transfer count
- [x] 7.9 Implement `tools/f1_fantasy.py` — `get_f1_fantasy_chips`: call authenticate_f1_fantasy to get session token, then `GET https://fantasy-api.formula1.com/partner_games/f1/boosters`; return available chip/booster status
- [x] 7.10 Implement `tools/fantasy.py` — `get_user_team`: delegate to `f1_fantasy.get_f1_fantasy_team()`; keep `get_user_team` as the tool name registered with AgentCore Gateway for agent graph compatibility
- [x] 7.11 Implement `tools/fantasy.py` — `get_current_prices`: delegate to `f1_fantasy.get_f1_fantasy_prices()`
- [x] 7.12 Implement `tools/fantasy.py` — `get_available_chips`: delegate to `f1_fantasy.get_f1_fantasy_chips()`
- [x] 7.15 Implement `tools/fantasy.py` — `get_active_rules`: call `Rule.find({"is_active": True}).to_list()` via Beanie, return each rule as a structured dict with `rule_type`, `name`, `description`, and a human-readable `constraint` string derived from `config` (e.g., `"Total team cost must not exceed 100.0M"`, `"Team must include exactly 5 drivers and 2 constructors"`) — this is read-only, no auth needed
- [x] 7.13 Implement `tools/submission.py` — `validate_team`: instantiate `RuleEngine`, call `rule_engine.validate_team(team, user_team_count)`, return validation result with any violations
- [x] 7.14 Implement `tools/submission.py` — `submit_team`: read `user_id` from ADK session state, call `TeamService.create_team()` or `TeamService.update_team()`; on success return persisted team ID and trigger `memory.write_recommendation_accepted(user_id, ...)`

## 8. ADK Agent Graph

- [x] 8.1 Implement `service/app/agent/agents.py` — define `F1DataAgent` (`LlmAgent`, Claude Haiku via Bedrock LiteLLM, tools from gateway: `get_live_session_data`, `get_historical_performance`); after tools complete, write results to short-term memory via `memory.write_session_context(session_id, "f1_data", results)`
- [x] 8.2 Define `IntelAgent` (`LlmAgent`, Claude Haiku, tools: `get_weather`, `get_odds`, `get_reddit_sentiment`); after tools complete, write results to short-term memory via `memory.write_session_context(session_id, "intel", results)`
- [x] 8.3 Define `FantasyContextAgent` (`LlmAgent`, Claude Haiku, tools: `get_user_team`, `get_current_prices`, `get_available_chips`, `get_active_rules`); after tools complete, write results to short-term memory via `memory.write_session_context(session_id, "fantasy_context", results)` — the `fantasy_context` key includes team state, prices, chip status, AND active rules
- [x] 8.4 Define `DataGathering` (`ParallelAgent`, `sub_agents=[F1DataAgent, IntelAgent, FantasyContextAgent]`)
- [x] 8.5 Define `SubmissionAgent` (`LlmAgent`, Claude Haiku, tools: `validate_team`, `submit_team`)
- [x] 8.6 Define root `F1FantasyAdvisor` (`LlmAgent`, model=Claude Sonnet via Bedrock, `sub_agents=[DataGathering, SubmissionAgent]`, memory adapter wired in); after `DataGathering` completes, reads all three short-term memory keys before synthesizing recommendation
- [x] 8.7 Write root agent system prompt: orchestration instructions, delegation rules, confirmation-before-submission constraint (wait for CopilotKit interrupt resolution before delegating to SubmissionAgent), data-first reasoning directive, confidence communication guidelines; include explicit rule-awareness directive: "Before proposing any team, read the `rules` field from `fantasy_context` in session memory and verify every pick satisfies all active constraints — budget cap, roster shape, DRS boost requirement, and driver eligibility"
- [ ] 8.8 Verify agent graph initializes without errors in a local test script with mocked tools

## 9. FastAPI Agent Router (AG-UI)

- [x] 9.1 Create `service/app/routers/agent.py` — expose the AG-UI protocol endpoint compatible with CopilotKit; extract `user_id` from validated JWT and inject into ADK session state before invoking the Runner
- [x] 9.2 Implement session creation: `POST /sessions` creates ADK session via Runner, returns `{ "session_id": "<uuid>" }` — requires valid Cognito JWT
- [x] 9.3 Implement AG-UI streaming endpoint: accepts message and session context, runs ADK Runner, streams AG-UI events (text deltas, tool call events, state updates) back to CopilotKit
- [x] 9.4 Add structured error handling: catch Runner exceptions, emit AG-UI error event, close stream
- [x] 9.5 Register the agent router in `service/app/main.py` under `/api/v1/agent` prefix
- [ ] 9.6 Manual test: confirm AG-UI stream returns agent response and tool call events to CopilotKit

## 10. Frontend — Auth

- [x] 10.1 Add Cognito SDK to the React app (`amazon-cognito-identity-js` or AWS Amplify Auth); Cognito user pool ID and client ID sourced from environment variables (set from CDK outputs) — NEVER hardcoded
- [x] 10.2 Create login page (`/login`): email + password form, calls Cognito `initiateAuth`, stores JWT and `user_id` in app state (Zustand or context)
- [x] 10.3 Create registration page (`/register`): email + password + confirm, calls Cognito `signUp` then `confirmSignUp`
- [x] 10.4 Implement auth route guard: redirect unauthenticated users away from `/advisor` to `/login`
- [x] 10.5 Add JWT to all API requests via an Axios/fetch interceptor — applies to `/api/v1/agent/` and all existing routes

## 11. Frontend — Chat Page (CopilotKit)

- [x] 11.1 Wrap the app with `<CopilotKit runtimeUrl="/api/v1/agent">` — configure AG-UI endpoint URL from environment variable
- [x] 11.2 Create `/advisor` route and page component; call `POST /api/v1/agent/sessions` on mount to obtain `session_id`, show error state if session creation fails
- [x] 11.3 Build chat UI using CopilotKit's `<CopilotSidebar>` or `<CopilotChat>` component — streaming responses handled by CopilotKit natively
- [x] 11.4 Build `MessageInput` component: text input + send button, CopilotKit disables input while stream is active and re-enables on stream close
- [x] 11.5 Handle stream errors: display error message in the thread and re-enable input

## 12. Frontend — Recommendation Card (Generative UI)

- [x] 12.1 Build `TeamRecommendationCard` component: displays 5 drivers, 2 constructors, DRS Boost pick, transfer diff (in/out) from current team, and chip advice
- [x] 12.2 Register `display_team_recommendation` tool with CopilotKit using `useRenderToolCall`: when the agent calls this tool, render `TeamRecommendationCard` inline in the chat thread with the structured payload (no text parsing required)
- [ ] 12.3 Implement "Apply Recommendation" button using CopilotKit Human-in-the-Loop: button resolves the CopilotKit interrupt, sending an explicit confirmation event that triggers `SubmissionAgent` — no raw text message sent

## 13. Integration & Testing

- [ ] 13.1 End-to-end test: register → login → open advisor → send recommendation request → all 3 parallel sub-agents fire and write to short-term memory → root agent reads all three keys → streams response with `TeamRecommendationCard` rendered via CopilotKit
- [ ] 13.2 Test partial failure: mock OpenF1 unavailable → agent acknowledges missing data and still produces a recommendation with reduced confidence
- [ ] 13.3 Test submission flow: click "Apply Recommendation" → CopilotKit interrupt resolved → `SubmissionAgent` validates team → submits → `write_recommendation_accepted` called → success message in chat thread
- [ ] 13.4 Test auth: unauthenticated request to any route (`/api/v1/agent/chat`, `/api/v1/teams/`, etc.) returns 401; expired token returns 401
- [ ] 13.5 Test memory: second session for same user → root agent context includes prior accepted recommendation from long-term memory written by `write_recommendation_accepted`
- [ ] 13.6 Test user_id isolation: `get_user_team` and `get_available_chips` must only return data for the authenticated user — verify tools read `user_id` from session state, not LLM arguments; verify F1 Fantasy API calls use the session token cached in ADK state, not a token passed by the LLM
- [ ] 13.7 Verify pre-commit hook blocks any commit containing a real API key value — confirm `secrets.local.env` cannot be staged
