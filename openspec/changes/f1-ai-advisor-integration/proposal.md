## Development Workflow

Every independent feature in this change must be developed in isolation:

1. **Worktree per feature** — create a dedicated git worktree for each independent feature section (e.g. one worktree for CDK infra, one for Cognito auth, one for AgentCore Gateway, etc.)
2. **Commit on completion** — once development of that feature is done, commit all changes with a clear, descriptive commit message scoped to that feature
3. **PR with description** — open a pull request with an appropriate title and description summarizing what was built, why, and any notable decisions
4. **Automerge** — the PR may be automerged as long as there are no merge conflicts; resolve any conflicts before merging

## Why

GridWise tracks F1 Fantasy teams and validates them against rules, but gives users no guidance on *what* to pick. An AI advisor that reasons over live session data, historical performance, weather, betting markets, and the user's current team state closes this gap — turning GridWise from a team tracker into an intelligent fantasy assistant.

## What Changes

- **New**: Multi-agent AI advisor embedded in the GridWise FastAPI service, powered by Google ADK + Claude via Bedrock (Sonnet for root agent, Haiku for sub-agents)
- **New**: AWS Cognito user pool for authentication — JWT validation middleware added to FastAPI applied to **all** routes; `user_id` injected into ADK session state (never passed as an LLM argument)
- **New**: AgentCore Gateway hosting all agent tools (external API tools + internal GridWise DB tools) — one gateway, one connection point for all sub-agents
- **New**: AgentCore Memory integration — long-term memory (preferences, chip history, past recommendations) read at session start, written post-session when a recommendation is accepted; short-term memory written by all three parallel sub-agents per session and read by the root agent
- **New**: `/api/v1/agent/` router in FastAPI — AG-UI protocol endpoint as the MVP entry point
- **New**: Chat page in the React frontend using CopilotKit — streaming via AG-UI protocol, Generative UI for recommendation cards, Human-in-the-Loop for submission confirmation
- **New**: `tools/f1_fantasy.py` — F1 Fantasy API client; `FantasyContextAgent` reads the user's actual F1 Fantasy team, live driver/constructor prices, and chip availability directly from `fantasy-api.formula1.com` instead of GridWise MongoDB
- **Replaced**: `service/app/agent/schemas/` and `service/app/agent/lambda/` (CDK Lambda-per-action-group architecture) removed and replaced by AgentCore Gateway-hosted tools
- **Replaced**: `service/app/agent/infra/f1-agent-stack.ts` — CDK Lambda stack removed; AgentCore Gateway + Memory are the new infrastructure
- **Modified**: All existing routes (`/api/v1/teams/`, `/api/v1/drivers/`, `/api/v1/constructors/`, `/api/v1/rules/`) now require a valid Cognito JWT — no breaking API contract changes, but unauthenticated access is no longer permitted

## Capabilities

### New Capabilities

- `ai-advisor-agent`: The multi-agent orchestration layer — root `F1FantasyAdvisor` LlmAgent (Sonnet) with parallel data-gathering sub-agents (Haiku) and a write-isolated submission agent, running embedded in FastAPI
- `agent-tools`: Tool implementations for each sub-agent — F1 live/historical data (OpenF1, Jolpica), external intelligence (weather, odds, Reddit), fantasy context (F1 Fantasy API via `tools/f1_fantasy.py` for live prices, user team, and chip status), and team submission (rule engine + team service via AgentCore Gateway)
- `f1-fantasy-api`: F1 Fantasy API client module — session token auth via F1 account credentials (Secrets Manager), live driver/constructor prices, user picked team, booster availability; isolated in `tools/f1_fantasy.py`
- `agentcore-memory`: AgentCore Memory adapter — long-term user memory (preferences, chip history, past recommendations) read at session start and written after recommendation accepted; short-term session memory written by all three parallel sub-agents and read by root agent
- `agentcore-gateway`: AgentCore Gateway hosting all 10 tools — single gateway for external API tools and internal GridWise DB tools alike
- `cognito-auth`: AWS Cognito user pool, JWT middleware in FastAPI (all routes), user_id propagation via ADK session state injection
- `agent-chat-api`: `/api/v1/agent/` FastAPI router with AG-UI protocol endpoint — backend entry point for CopilotKit frontend
- `chat-ui`: React chat page using CopilotKit — streaming responses via AG-UI, `TeamRecommendationCard` rendered via `useRenderToolCall` on `display_team_recommendation` tool calls, submission confirmation via CopilotKit Human-in-the-Loop

### Modified Capabilities

- `teams`: No requirement changes — existing `TeamService` and `RuleEngine` are called by agent tools via AgentCore Gateway; existing REST endpoints now require Cognito JWT

## Impact

- **New dependencies**: `google-adk`, `litellm`, `boto3` (Bedrock), `amazon-agentcore` (Memory + Gateway client), `python-jose` (JWT validation), `httpx` (F1 Fantasy API calls); frontend: `@copilotkit/react-core`, `@copilotkit/react-ui`
- **New file**: `service/app/agent/tools/f1_fantasy.py` — F1 Fantasy API client (auth, prices, team, chips)
- **New secrets**: `gridwise/f1-credentials` in Secrets Manager (`F1_USERNAME`, `F1_PASSWORD`); added to `secrets.local.env`
- **AWS**: Cognito user pool, AgentCore Gateway resource, AgentCore Memory store — all new
- **`service/app/agent/`**: Directory repurposed — `schemas/`, `lambda/`, `infra/` removed; replaced with `agents.py`, `memory.py`, `gateway.py`, `tools/`
- **`service/app/main.py`**: New agent router registered, Cognito auth middleware added and applied to all routes
- **`service/app/routers/`**: New `agent.py` router
- **`service/app/auth.py`**: New — JWT validation and `get_current_user` FastAPI dependency
- **Frontend**: New chat page with CopilotKit; existing pages gain auth guard
- **Breaking auth change**: All existing endpoints now require `Authorization: Bearer <jwt>` — clients that previously called routes without auth will receive 401
