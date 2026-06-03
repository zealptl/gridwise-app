## Implementation Workflow

Each numbered task group (1, 2, 3, …) is an independent unit of work. Follow this process for every group:

1. **Create a git worktree** for the task group:
   ```bash
   git worktree add ../gridwise-<group-slug> -b feat/<group-slug>
   ```
   Example: `git worktree add ../gridwise-cognito-tier -b feat/cognito-tier`

2. **Implement all tasks in that group** inside the worktree.

3. **No secrets in commits** — API keys, tokens, passwords, and credentials SHALL NOT appear in any committed file. Use AWS Secrets Manager (already provisioned in CDK) or SSM Parameter Store. If a file accidentally contains a secret, remove it before committing and rotate the credential immediately.

4. **Commit to the feature branch** with a conventional commit message:
   ```bash
   git commit -m "feat: <short description of the task group>"
   ```

5. **Push and open a PR** targeting `main`:
   ```bash
   git push -u origin feat/<group-slug>
   gh pr create --title "feat: <group name>" --base main
   ```

6. **Merge the PR** before starting the next task group. Task groups have dependencies — do not begin a downstream group until its upstream PR is merged and `main` is up to date.

7. **Remove the worktree** after merge:
   ```bash
   git worktree remove ../gridwise-<group-slug>
   ```

---

## 1. Cognito Tier Attribute

- [ ] 1.1 Add `custom:tier` custom attribute to Cognito user pool in `gridwise-agent-stack.ts` (string, mutable, allowed values: `free`, `premium`)
- [ ] 1.2 Update `/auth/register` endpoint to set `custom:tier = "free"` on new user creation via Cognito AdminUpdateUserAttributes
- [ ] 1.3 Add `get_user_tier(jwt_token: str) -> str` utility to `auth.py` that decodes the JWT and returns `custom:tier`, defaulting to `"free"` if absent

## 2. FastAPI Tool Endpoints

- [ ] 2.1 Create `service/app/routers/agent_tools.py` with IAM SigV4 auth middleware for all `/agent/tools/*` routes
- [ ] 2.2 Add endpoint `POST /agent/tools/get-live-session-data` — calls `get_live_session_data()` from `tools/f1_data.py`
- [ ] 2.3 Add endpoint `POST /agent/tools/get-historical-performance` — calls `get_historical_performance()` from `tools/f1_data.py`
- [ ] 2.4 Add endpoint `POST /agent/tools/get-weather` — calls `get_weather(circuit_location)` from `tools/intelligence.py`
- [ ] 2.5 Add endpoint `POST /agent/tools/get-odds` — calls `get_odds()` from `tools/intelligence.py`
- [ ] 2.6 Add endpoint `POST /agent/tools/get-reddit-sentiment` — calls `get_reddit_sentiment(race_name)` from `tools/intelligence.py`
- [ ] 2.7 Add endpoint `POST /agent/tools/get-user-team` — calls `get_user_team(session_state)` from `tools/fantasy.py`
- [ ] 2.8 Add endpoint `POST /agent/tools/get-current-prices` — calls `get_current_prices()` from `tools/fantasy.py`
- [ ] 2.9 Add endpoint `POST /agent/tools/get-available-chips` — calls `get_available_chips(session_state)` from `tools/fantasy.py`
- [ ] 2.10 Add endpoint `POST /agent/tools/get-active-rules` — calls `get_active_rules()` from `tools/fantasy.py`
- [ ] 2.11 Add endpoint `POST /agent/tools/validate-team` — calls `validate_team(team, user_team_count)` from `tools/submission.py`
- [ ] 2.12 Add endpoint `POST /agent/tools/submit-team` — enforces `validated: true` in request body before calling `submit_team(session_state, team)` from `tools/submission.py`
- [ ] 2.13 Register `agent_tools` router in `main.py`

## 3. AgentCore Gateway CDK

- [ ] 3.1 Add `AWS::BedrockAgentCore::Gateway` CfnResource to `gridwise-agent-stack.ts` with name `gridwise-agent-gateway`
- [ ] 3.2 Register all 11 tools on the gateway — each with name, description (from existing `schemas/*.json`), input schema, and FastAPI endpoint URL as the HTTP handler
- [ ] 3.3 Configure tier access policies: `get_weather`, `get_odds`, `get_reddit_sentiment` require `custom:tier: "premium"`; all other tools accessible to any authenticated user
- [ ] 3.4 Configure gateway to call FastAPI endpoints using `gridwise-fastapi-service-role` IAM credentials (SigV4)
- [ ] 3.5 Write deployed gateway endpoint URL to SSM parameter `/gridwise/agentcore/gateway-endpoint` as a CDK output + StringParameter
- [ ] 3.6 Run `cdk deploy` and verify gateway is created and all 11 tools are listed via `aws bedrock-agentcore list-gateway-tools`

## 4. gateway.py Rewrite

- [ ] 4.1 Update `AgentCoreGateway.__init__` to accept `jwt: str | None = None` and store it
- [ ] 4.2 Rewrite `get_toolset_for_agent` to use semantic discovery mode — pass `discovery_query` (sub-agent description) and inject `Authorization: Bearer <jwt>` header on the `MCPToolset` connection
- [ ] 4.3 Remove `TOOL_REGISTRY` dict and `get_toolset` convenience wrapper (no longer needed with semantic discovery)
- [ ] 4.4 Update `verify_gateway_connection` to test with a sample semantic query and confirm tools are returned

## 5. agents.py Updates

- [ ] 5.1 Update `build_f1_advisor_graph()` to accept `user_jwt: str | None` and pass it to `AgentCoreGateway(jwt=user_jwt)`
- [ ] 5.2 Rewrite `_build_f1_data_agent` — remove `tool_names` from toolset call; use agent description as semantic query; enrich `instruction` with: data format expectations, memory key (`f1_data`), failure handling when APIs return `available: false`
- [ ] 5.3 Rewrite `_build_intel_agent` — remove `tool_names`; use description as semantic query; enrich `instruction` with: how to handle empty toolset (free-tier user), memory key (`intel`), what to write when no tools available
- [ ] 5.4 Rewrite `_build_fantasy_context_agent` — remove `tool_names`; enrich `instruction` with: expected memory key (`fantasy_context`), required sub-fields (`team`, `prices`, `chips`, `rules`), null handling for unavailable fields
- [ ] 5.5 Rewrite `_build_submission_agent` — remove `tool_names`; enrich `instruction` with: validate-before-submit enforcement, violation response format, what to return on success vs failure
- [ ] 5.6 Update root `ADVISOR_SYSTEM_PROMPT` to describe free vs premium tool availability and how to present degraded recommendations to free-tier users

## 6. Chat Endpoint JWT Forwarding

- [ ] 6.1 Update the chat API endpoint in `main.py` to extract the raw JWT string from the `Authorization: Bearer` header
- [ ] 6.2 Pass the JWT to `build_f1_advisor_graph(user_jwt=token)` when creating the agent session
- [ ] 6.3 Return HTTP 401 if no `Authorization` header is present on the chat endpoint

## 7. Verification

- [ ] 7.1 Test with a free-tier user JWT: confirm only 8 tools are returned by semantic discovery, intelligence tools absent
- [ ] 7.2 Test with a premium-tier user JWT: confirm all 11 tools are returned
- [ ] 7.3 Test end-to-end chat request: free user asks for recommendation → F1DataAgent + FantasyContextAgent gather data → IntelAgent gracefully skips → advisor returns recommendation with reduced-confidence note
- [ ] 7.4 Test end-to-end chat request: premium user asks for recommendation → all 3 parallel agents gather data → full recommendation returned
- [ ] 7.5 Test unauthenticated chat request returns HTTP 401
