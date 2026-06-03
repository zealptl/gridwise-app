# AI Advisor Agent Flow

Multi-agent architecture for the F1 Fantasy AI Advisor. Powered by Google ADK embedded in the FastAPI service, using AWS AgentCore for memory and gateway infrastructure.

---

## Activity Diagram

End-to-end user journey from opening the chat to a submitted team, including all decision branches.

```plantuml
@startuml
skinparam ActivityBackgroundColor #F8F9FA
skinparam ActivityBorderColor #6C757D
skinparam ActivityDiamondBackgroundColor #FFF3CD
skinparam ActivityDiamondBorderColor #FFC107
skinparam ArrowColor #495057
skinparam roundcorner 8

start

:User opens /advisor page;
:Frontend calls POST /api/v1/agent/sessions;

if (JWT valid?) then (no)
  #FFB3B3:Return 401 Unauthorized;
  stop
else (yes)
  :Extract user_id from Cognito sub claim;
  :Inject user_id into ADK session state;
  :Return session_id to frontend;
endif

:User sends recommendation request;
:Root agent (F1FantasyAdvisor) starts;

:Read long-term memory\n(prior picks, chip history, preferences);

note right
  Empty for new users.
  Informs root agent of past decisions
  before data gathering begins.
end note

fork
  :F1DataAgent;
  :get_live_session_data (OpenF1);
  :get_historical_performance (Jolpica);
  :Write → short-term memory "f1_data";
fork again
  :IntelAgent;
  :get_weather (WeatherAPI);
  :get_odds (Odds API);
  :get_reddit_sentiment (Reddit);
  :Write → short-term memory "intel";
fork again
  :FantasyContextAgent;
  :get_user_team (F1 Fantasy API);
  :get_current_prices (F1 Fantasy API);
  :get_available_chips (F1 Fantasy API);
  :get_active_rules (GridWise MongoDB);
  :Write → short-term memory "fantasy_context"\n(team + prices + chips + rules);
end fork

if (All sub-agents succeeded?) then (partial failure)
  :Note unavailable data sources;
  :Proceed with reduced confidence;
else (yes)
endif

:Root agent reads all three\nshort-term memory keys;

:Check active rules from fantasy_context\n(budget cap, roster shape, DRS boost,\neligibility constraints);

note right
  Rules are checked BEFORE
  synthesising any picks.
  Prevents rule violations at
  the recommendation stage.
end note

:Synthesise team recommendation\n(5 drivers, 2 constructors, DRS boost,\ntransfer diff, chip advice);

:Call display_team_recommendation →\nCopilotKit renders TeamRecommendationCard;

if (User confirms recommendation?) then (declines / asks to revise)
  :Root agent adjusts recommendation\nbased on user feedback;
  :Re-display updated card;
  if (User confirms revised recommendation?) then (declines again)
    :End session without submission;
    stop
  else (confirms)
  endif
else (confirms)
endif

:Delegate to SubmissionAgent;
:validate_team via RuleEngine;

if (Team passes validation?) then (violations found)
  note right
    Edge case — should rarely occur
    since rules were checked at synthesis.
    Triggered by price drift or
    arithmetic errors.
  end note
  :Return violations to root agent;
  :Root agent revises recommendation;
  :Re-display updated card;
  :validate_team again;
else (valid)
endif

:submit_team via TeamService;

if (Submission successful?) then (error)
  #FFB3B3:Surface error in chat thread;
  stop
else (success)
endif

:Write to long-term memory\n(accepted picks, chips used, preferences);

#B3FFB3:Show success message in chat thread;

stop
@enduml
```

---

## Data Flow Diagram

How data moves through the agent graph — from external APIs through short-term memory to the root agent's synthesis and final submission.

```plantuml
@startuml
skinparam componentStyle rectangle
skinparam backgroundColor #FFFFFF
skinparam ArrowColor #495057
skinparam ComponentBackgroundColor #F8F9FA
skinparam ComponentBorderColor #6C757D
skinparam DatabaseBackgroundColor #FFF0F0
skinparam DatabaseBorderColor #DC3545
skinparam NodeBackgroundColor #F0F4FF
skinparam NodeBorderColor #4361EE
skinparam CloudBackgroundColor #F0FFF0
skinparam CloudBorderColor #2DC653
skinparam NoteBackgroundColor #FFFDE7
skinparam NoteBorderColor #FFC107
skinparam roundcorner 8

together {
  cloud "OpenF1 API" as F1API #F0FFF0
  cloud "Jolpica API" as JolpicaAPI #F0FFF0
}

together {
  cloud "WeatherAPI" as WeatherAPI #F0FFF0
  cloud "Odds API" as OddsAPI #F0FFF0
  cloud "Reddit API" as RedditAPI #F0FFF0
}

together {
  cloud "F1 Fantasy API\n(prices, team, chips)" as FFApi #F0FFF0
  database "GridWise MongoDB\n(rules)" as MongoDB #FFF0F0
}

node "F1DataAgent\n(Haiku)" as FDA #F0F4FF
node "IntelAgent\n(Haiku)" as IA #F0F4FF
node "FantasyContextAgent\n(Haiku)" as FCA #F0F4FF

database "AgentCore\nShort-Term Memory" as STM #FFF4E0 {
  [f1_data]
  [intel]
  [fantasy_context\n(team · prices · chips · rules)]
}

database "AgentCore\nLong-Term Memory" as LTM #FFF4E0

node "F1FantasyAdvisor\n(Root Agent / Sonnet)" as Root #E8F5E9

node "SubmissionAgent\n(Haiku)" as SA #F0F4FF

database "GridWise MongoDB\n(TeamService, RuleEngine)" as MongoDB2 #FFF0F0

component "CopilotKit\nTeamRecommendationCard" as CK #FCE4EC

F1API --> FDA : live session data
JolpicaAPI --> FDA : historical standings
FDA --> [f1_data] : write

WeatherAPI --> IA : 3-day forecast
OddsAPI --> IA : implied win probabilities
RedditAPI --> IA : community sentiment
IA --> [intel] : write

FFApi --> FCA : team, prices, chips
MongoDB --> FCA : active rules
FCA --> [fantasy_context\n(team · prices · chips · rules)] : write

LTM --> Root : prior picks\n& preferences\n(session start)

[f1_data] --> Root : read (post DataGathering)
[intel] --> Root : read (post DataGathering)
[fantasy_context\n(team · prices · chips · rules)] --> Root : read (post DataGathering)

Root --> CK : display_team_recommendation\n(structured payload)
Root --> SA : delegate on user confirmation

SA --> MongoDB2 : validate_team (RuleEngine)\nsubmit_team (TeamService)
SA --> LTM : write accepted recommendation\n(post submission)
@enduml
```

---

## Full Session Flow

```plantuml
@startuml
skinparam sequenceArrowThickness 1.5
skinparam participantPadding 10
skinparam boxPadding 10
skinparam roundcorner 8

actor User
participant "CopilotKit\n(React)" as CK
participant "FastAPI\n/api/v1/agent" as API
participant "JWT Middleware\n(Cognito)" as Auth

box "ADK Agent Graph" #F0F4FF
  participant "F1FantasyAdvisor\n(Root Agent / Sonnet)" as Root
  participant "DataGathering\n(ParallelAgent)" as DG
  participant "F1DataAgent\n(Haiku)" as FDA
  participant "IntelAgent\n(Haiku)" as IA
  participant "FantasyContextAgent\n(Haiku)" as FCA
  participant "SubmissionAgent\n(Haiku)" as SA
end box

box "AgentCore" #FFF4E0
  participant "Gateway\n(Tool Host)" as GW
  participant "Short-Term\nMemory" as STM
  participant "Long-Term\nMemory" as LTM
end box

box "External APIs" #F0FFF0
  participant "OpenF1 API" as F1
  participant "Jolpica API" as JO
  participant "WeatherAPI" as WA
  participant "Odds API" as OA
  participant "Reddit API" as RD
  participant "F1 Fantasy API" as FF
end box

box "GridWise DB" #FFF0F0
  participant "MongoDB\n(Rules, Teams)" as DB
end box

== Session Start ==

User -> CK : Open advisor chat
CK -> API : POST /api/v1/agent/sessions
API -> Auth : Validate JWT (Bearer token)
Auth --> API : user_id (Cognito sub claim)
API --> CK : { session_id }

== User Sends Message ==

User -> CK : "Recommend a team for this weekend"
CK -> API : AG-UI stream request\n{ message, session_id }
API -> Auth : Validate JWT
Auth --> API : user_id
API -> Root : Inject user_id into\nADK session state\nStart Runner

== Root Agent: Session Initialisation ==

Root -> LTM : read_long_term_memory(user_id)
LTM --> Root : Prior picks, chips used,\nstated preferences (empty for new user)

== Parallel Data Gathering ==

Root -> DG : Delegate to DataGathering

par F1DataAgent
  DG -> FDA : Start
  FDA -> GW : get_live_session_data
  GW -> F1 : GET /sessions, /laps,\n/stints, /weather, /race_control
  F1 --> GW : Live session data
  GW --> FDA : Structured dict
  FDA -> GW : get_historical_performance
  GW -> JO : GET standings,\nlast-3-race results
  JO --> GW : Historical data
  GW --> FDA : Structured dict
  FDA -> STM : write_session_context\n(session_id, "f1_data", results)

else IntelAgent
  DG -> IA : Start
  IA -> GW : get_weather
  GW -> WA : GET 3-day forecast\n(circuit location)
  WA --> GW : Weather data
  GW --> IA : Forecast dict
  IA -> GW : get_odds
  GW -> OA : GET F1 race winner market
  OA --> GW : Odds → implied probabilities
  GW --> IA : Probabilities dict
  IA -> GW : get_reddit_sentiment
  GW -> RD : GET r/formula1,\nr/FantasyF1 posts
  RD --> GW : Recent discussions
  GW --> IA : Sentiment summary
  IA -> STM : write_session_context\n(session_id, "intel", results)

else FantasyContextAgent
  DG -> FCA : Start
  FCA -> GW : get_user_team
  GW -> FF : GET /picked_teams\n?my_current_picked_teams=true
  FF --> GW : Current team composition,\nbudget, transfer count
  GW --> FCA : Team dict
  FCA -> GW : get_current_prices
  GW -> FF : GET /players, GET /teams
  FF --> GW : Live driver &\nconstructor prices
  GW --> FCA : Prices dict
  FCA -> GW : get_available_chips
  GW -> FF : GET /boosters
  FF --> GW : Chip availability
  GW --> FCA : Chips dict
  FCA -> GW : get_active_rules
  GW -> DB : Rule.find(is_active=True)
  DB --> GW : Active rules\n(budget cap, roster size,\nDRS boost, eligibility, etc.)
  GW --> FCA : Rules as human-readable\nconstraint descriptions
  FCA -> STM : write_session_context\n(session_id, "fantasy_context",\n{ team, prices, chips, rules })
end

DG --> Root : All sub-agents complete

== Root Agent: Synthesis ==

Root -> STM : read_session_context(session_id, "f1_data")
Root -> STM : read_session_context(session_id, "intel")
Root -> STM : read_session_context(session_id, "fantasy_context")
STM --> Root : All gathered context

note over Root
  Synthesises recommendation.
  Checks active rules (budget cap,
  roster shape, DRS boost, eligibility)
  BEFORE proposing any picks.
end note

Root -> CK : call display_team_recommendation\n{ drivers, constructors, DRS boost,\ntransfer diff, chip advice }
CK --> User : Render TeamRecommendationCard\n(inline in chat thread)
Root -> CK : AG-UI stream: pause\n(await user confirmation)

== User Confirms ==

User -> CK : Click "Apply Recommendation"
CK -> API : CopilotKit interrupt resolved
API -> Root : Confirmation event received

== Submission ==

Root -> SA : Delegate to SubmissionAgent

SA -> GW : validate_team(proposed_team)
GW -> DB : RuleEngine.validate_team()
DB --> GW : Validation result
GW --> SA : Pass / Fail + violations

alt Team is valid
  SA -> GW : submit_team(user_id, proposed_team)
  GW -> DB : TeamService.create_team()\nor update_team()
  DB --> GW : Persisted team ID
  GW --> SA : Success + team_id
  SA -> LTM : write_recommendation_accepted\n(user_id, picks, chips_used, preferences)
  SA --> Root : Submission confirmed
  Root -> CK : AG-UI stream: success message
  CK --> User : "Team applied successfully!"
else Team is invalid
  SA --> Root : Validation failed + violations
  Root -> CK : AG-UI stream: explain violations,\nrevise recommendation
  CK --> User : Updated recommendation
end

@enduml
```

## Agent Roles

| Agent | Model | Tools | Memory Write |
|---|---|---|---|
| `F1FantasyAdvisor` | Claude Sonnet (Bedrock) | — (delegates only) | Reads long-term at start |
| `F1DataAgent` | Claude Haiku (Bedrock) | `get_live_session_data`, `get_historical_performance` | `f1_data` → short-term |
| `IntelAgent` | Claude Haiku (Bedrock) | `get_weather`, `get_odds`, `get_reddit_sentiment` | `intel` → short-term |
| `FantasyContextAgent` | Claude Haiku (Bedrock) | `get_user_team`, `get_current_prices`, `get_available_chips`, `get_active_rules` | `fantasy_context` → short-term |
| `SubmissionAgent` | Claude Haiku (Bedrock) | `validate_team`, `submit_team` | `recommendation_accepted` → long-term |

## Tool Sources

| Tool | Source | Auth |
|---|---|---|
| `get_live_session_data` | OpenF1 API | None (public) |
| `get_historical_performance` | Jolpica API | None (public) |
| `get_weather` | WeatherAPI | API key (Secrets Manager) |
| `get_odds` | The Odds API | API key (Secrets Manager) |
| `get_reddit_sentiment` | Reddit OAuth API | Client credentials (Secrets Manager) |
| `get_user_team` | F1 Fantasy API | F1 session token (Secrets Manager) |
| `get_current_prices` | F1 Fantasy API | None (public endpoint) |
| `get_available_chips` | F1 Fantasy API | F1 session token (Secrets Manager) |
| `get_active_rules` | GridWise MongoDB | None (internal) |
| `validate_team` | GridWise RuleEngine | None (internal) |
| `submit_team` | GridWise TeamService | None (internal) |

## Key Design Decisions

- **`user_id` is never an LLM argument** — extracted from JWT in FastAPI middleware and injected directly into ADK session state before the Runner starts. Tools read it from session context, preventing prompt injection attacks.
- **Rules loaded before synthesis** — `get_active_rules` runs in parallel during `FantasyContextAgent`. Root agent reads rules from short-term memory before proposing any picks, eliminating the validate→revise loop for rule violations.
- **`validate_team` is a safety net, not the primary constraint** — the agent already knows the rules. Validation at submission time catches edge cases (price drift, arithmetic errors) not reasoning failures.
- **Long-term memory written only on accepted recommendations** — past picks, chip usage, and stated preferences are persisted after `submit_team` succeeds. Sessions where no team is submitted leave long-term memory unchanged.
