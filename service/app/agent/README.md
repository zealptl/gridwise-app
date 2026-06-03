# F1 Fantasy Predictor — AWS Bedrock Agent

An AI-powered F1 Fantasy team advisor built on **Amazon Bedrock Agents** that makes empirically-grounded team recommendations by connecting to real-time F1 data APIs, community intelligence, weather forecasts, and betting markets.

## Project Structure

```
f1-agent/
├── schemas/                              # OpenAPI schemas for Bedrock Action Groups
│   ├── get-live-session-data.json        # OpenF1 API integration
│   ├── get-fantasy-data.json             # F1 Fantasy API + User Team API
│   └── run-prediction-engine.json        # ML prediction + team optimizer
│
├── lambda/                               # Lambda function handlers
│   └── run-prediction-engine/
│       └── handler.py                    # Python ML model with Monte Carlo simulation
│
├── infra/
│   └── f1-agent-stack.ts                 # CDK infrastructure (all resources)
│
└── README.md                             # This file
```

## Architecture Overview

```
User → Bedrock Agent (Claude 3.5 Sonnet)
              │
              ├─→ Action Group 1: GetLiveSessionData
              │     └─→ Lambda → OpenF1 API (lap times, telemetry, weather, stints)
              │
              ├─→ Action Group 2: GetHistoricalPerformance
              │     └─→ Lambda → Jolpica-F1 API (results, standings, reliability)
              │
              ├─→ Action Group 3: GetFantasyData
              │     └─→ Lambda → F1 Fantasy API + Your User Team API
              │
              ├─→ Action Group 4: GetExternalIntelligence
              │     └─→ Lambda → WeatherAPI + Odds API + Reddit API + RSS
              │
              ├─→ Action Group 5: RunPredictionEngine
              │     └─→ Lambda → ML Model + Monte Carlo + Team Optimizer
              │
              ├─→ Action Group 6: ValidateAndSubmit
              │     └─→ Lambda → Your Custom Validation Engine
              │
              └─→ Knowledge Base (RAG)
                    └─→ S3 + OpenSearch Serverless
                          ├── F1 Fantasy 2026 scoring rules
                          ├── Circuit profiles (all 24 tracks)
                          ├── Driver/constructor profiles
                          └── Strategy playbooks
```

## Deployment Steps

### Prerequisites

- AWS Account with Bedrock access (Claude models enabled)
- AWS CDK v2 installed
- Node.js 20+ and Python 3.12+
- API keys for: WeatherAPI, The Odds API, Reddit

### Step 1: Deploy Infrastructure

```bash
cd infra
npm install
cdk bootstrap
cdk deploy
```

This creates:
- 6 Lambda functions (one per Action Group)
- S3 buckets for schemas and Knowledge Base docs
- Secrets Manager entries (populate after deployment)
- IAM roles for Agent and Lambdas

### Step 2: Populate Secrets

```bash
# OpenF1 (only needed for real-time data)
aws secretsmanager put-secret-value \
  --secret-id f1-agent/openf1-credentials \
  --secret-string '{"username":"YOUR_USER","password":"YOUR_PASS"}'

# WeatherAPI
aws secretsmanager put-secret-value \
  --secret-id f1-agent/weather-api-key \
  --secret-string '{"api_key":"YOUR_KEY"}'

# The Odds API
aws secretsmanager put-secret-value \
  --secret-id f1-agent/odds-api-key \
  --secret-string '{"api_key":"YOUR_KEY"}'

# Reddit
aws secretsmanager put-secret-value \
  --secret-id f1-agent/reddit-credentials \
  --secret-string '{"client_id":"YOUR_ID","client_secret":"YOUR_SECRET"}'

# F1 Fantasy (extract from browser DevTools)
aws secretsmanager put-secret-value \
  --secret-id f1-agent/f1-fantasy-credentials \
  --secret-string '{"token":"YOUR_BEARER_TOKEN","user_guid":"YOUR_GUID"}'
```

### Step 3: Create the Bedrock Agent

In the AWS Bedrock Console:

1. **Create Agent** → Name: "F1 Fantasy Advisor"
2. **Foundation Model** → Anthropic Claude 3.5 Sonnet v2
3. **Agent Instructions** → Paste the system prompt (see below)
4. **Add Action Groups** (6 total):
   - For each, select the corresponding Lambda function
   - Upload the OpenAPI schema from S3 (or use simplified function defs)
5. **Create Knowledge Base**:
   - Data source: S3 bucket (knowledge-base bucket)
   - Vector store: OpenSearch Serverless
   - Embeddings: Titan Embeddings v2
6. **Attach Knowledge Base** to the Agent
7. **Create Alias** → "production"
8. **Test** in the built-in console

### Step 4: Agent Instructions (System Prompt)

```
You are an F1 Fantasy Team Advisor. You build optimal fantasy teams
backed by EMPIRICAL DATA from real F1 sessions, not general knowledge.

WORKFLOW (follow this order):
1. GATHER: Call GetLiveSessionData for the current race weekend's
   practice pace, qualifying times, and session weather.
2. ENRICH: Call GetHistoricalPerformance for driver/circuit history,
   constructor form, reliability stats, and pit stop performance.
3. CONTEXT: Call GetExternalIntelligence for weather forecasts,
   betting odds, Reddit sentiment on upgrades/penalties, and news.
4. FANTASY: Call GetFantasyData for current prices, the user's
   existing team, budget, available chips, and transfers.
5. PREDICT: Call RunPredictionEngine with ALL gathered data.
   Request Monte Carlo simulation for confidence intervals.
6. VALIDATE: Call ValidateAndSubmit to check the proposed team
   against the rules engine before presenting to the user.
7. EXPLAIN: Present the recommendation with:
   - Each pick justified by specific data (cite the source)
   - Confidence level and point range
   - Transfers needed from current team and any penalties
   - DRS Boost recommendation with reasoning
   - Chip timing advice for upcoming races

CONSTRAINTS (2026 Rules):
- Budget cap: $100M
- Roster: 5 drivers + 2 constructors
- Transfers: 2 free per race weekend, extras cost -10 pts each
- DRS Boost: Assign to one driver (doubles their score)
- Chips: Limitless, Wildcard, No Negative, 3x Boost, Autopilot, Final Fix

IMPORTANT:
- NEVER recommend picks based solely on your training data.
- ALWAYS call the data APIs first, then reason over the results.
- When uncertain, say so and show the confidence interval.
- If practice data is not yet available (pre-weekend), state that
  predictions are based on historical patterns only (~65% confidence).
```

## API Quick Reference

| API               | Base URL                                               | Auth             | Cost     |
|-------------------|--------------------------------------------------------|------------------|----------|
| OpenF1            | `https://api.openf1.org/v1`                            | None / Bearer    | Free*    |
| Jolpica-F1        | `https://api.jolpi.ca/ergast/f1`                       | None             | Free     |
| F1 Fantasy        | `https://fantasy-api.formula1.com/partner_games/f1`    | Bearer token     | Free     |
| WeatherAPI        | `https://api.weatherapi.com/v1`                        | API key (query)  | Free**   |
| The Odds API      | `https://api.the-odds-api.com/v4`                      | API key (query)  | Free**   |
| Reddit            | `https://oauth.reddit.com`                             | OAuth2 Bearer    | Free     |

\* Historical data free; real-time requires paid subscription
\** Free tier sufficient for F1 usage

## Prediction Model Features

The ML model uses these features (ranked by importance):

| Feature                    | Weight | Source              |
|----------------------------|--------|---------------------|
| Clean air race pace        | 95%    | OpenF1 / FastF1     |
| Mechanical reliability     | 85%    | Jolpica-F1          |
| Qualifying position        | 82%    | OpenF1              |
| Pit stop efficiency        | 72%    | Jolpica-F1          |
| Team/constructor form      | 68%    | Jolpica-F1          |
| Tyre strategy/degradation  | 55%    | OpenF1 stints       |
| Rain probability           | 45%    | WeatherAPI          |
| First-lap incident prob.   | 40%    | Historical data     |
| Track temperature          | 38%    | OpenF1 / WeatherAPI |
| Safety car probability     | 28%    | Historical data     |
| Betting implied probability| 25%    | The Odds API        |

## Next Steps

1. **Train the ML model**: Gather 2-3 seasons of data via Jolpica + OpenF1, engineer features, train a `GradientBoostingRegressor` or `XGBRanker`, serialize with pickle, upload to S3.

2. **Build the Knowledge Base**: Create markdown/PDF documents for scoring rules, circuit profiles, and strategy guides. Upload to the KB S3 bucket.

3. **Wire up YOUR APIs**: Replace `YOUR_CUSTOM_API_URL_HERE` and `YOUR_VALIDATION_ENGINE_URL_HERE` in the CDK stack with your actual user team tracking and validation engine endpoints.

4. **Test incrementally**: Start with just the OpenF1 + Jolpica action groups. Verify the agent can reason over real data. Then add external intelligence and the prediction engine.

5. **Monitor and improve**: Use Bedrock Agent traces to see which tools the agent calls and how it reasons. Tune the system prompt based on observed behavior.
