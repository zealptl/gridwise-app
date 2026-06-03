"""
F1 Fantasy Advisor agent graph.
Uses Google ADK with Claude via Bedrock (LiteLLM bridge).
"""
import logging

logger = logging.getLogger(__name__)

HAIKU = "bedrock/anthropic.claude-3-haiku-20240307-v1:0"
SONNET = "bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0"

ADVISOR_SYSTEM_PROMPT = """You are the GridWise F1 Fantasy Advisor — an expert AI assistant that helps users optimise their F1 Fantasy team.

ORCHESTRATION RULES:
1. When a user asks for a recommendation, FIRST delegate to DataGathering to collect all necessary data in parallel.
2. After DataGathering completes, read all three session memory keys: f1_data, intel, fantasy_context.
3. Synthesise a recommendation based on ALL gathered data.
4. Present your recommendation using the display_team_recommendation tool with structured data.
5. WAIT for the user to explicitly confirm before delegating to SubmissionAgent.
6. Only delegate to SubmissionAgent after receiving explicit user confirmation.

RULE COMPLIANCE:
Before proposing any team, read the `rules` field from `fantasy_context` in session memory and verify every pick satisfies all active constraints — budget cap, roster shape, DRS boost requirement, and driver eligibility. Never propose a team that violates an active rule.

REASONING APPROACH:
- Lead with data: cite specific stats from f1_data and intel to justify every pick.
- Acknowledge missing data: if an API was unavailable, state this and reduce confidence accordingly.
- Be explicit about uncertainty: use phrases like "based on available data" or "with reduced confidence" when data is incomplete.

SUBMISSION CONSTRAINT:
NEVER call SubmissionAgent without explicit user confirmation. The user must actively choose to apply the recommendation.
"""


def _build_f1_data_agent(gateway, memory):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent("f1_data_agent", ["get_live_session_data", "get_historical_performance"])
    return LlmAgent(
        name="F1DataAgent",
        model=LiteLlm(model=HAIKU),
        description="Fetches live F1 session data and historical driver/constructor performance.",
        instruction=(
            "Gather F1 performance data. Use get_live_session_data for the latest session "
            "and get_historical_performance for standings and recent results. "
            "After gathering all data, write results to session memory with key 'f1_data'. "
            "Return a structured summary."
        ),
        tools=toolset or [],
    )


def _build_intel_agent(gateway, memory):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent("intel_agent", ["get_weather", "get_odds", "get_reddit_sentiment"])
    return LlmAgent(
        name="IntelAgent",
        model=LiteLlm(model=HAIKU),
        description="Gathers external intelligence: weather, betting odds, and Reddit sentiment.",
        instruction=(
            "Gather external race intelligence. Use get_weather for circuit forecast, "
            "get_odds for race winner probabilities, get_reddit_sentiment for community picks. "
            "Write results to session memory with key 'intel'. Return a structured summary."
        ),
        tools=toolset or [],
    )


def _build_fantasy_context_agent(gateway, memory):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent(
        "fantasy_context_agent",
        ["get_user_team", "get_current_prices", "get_available_chips", "get_active_rules"],
    )
    return LlmAgent(
        name="FantasyContextAgent",
        model=LiteLlm(model=HAIKU),
        description="Loads the user's current fantasy team, live prices, chip availability, and active rules.",
        instruction=(
            "Load the user's fantasy context. Use get_user_team for their current picks, "
            "get_current_prices for live driver/constructor prices, get_available_chips for chip status, "
            "and get_active_rules for all active constraints. "
            "Write results (including rules) to session memory with key 'fantasy_context'. "
            "Return a structured summary."
        ),
        tools=toolset or [],
    )


def _build_data_gathering_agent(gateway, memory):
    from google.adk.agents import ParallelAgent  # type: ignore

    return ParallelAgent(
        name="DataGathering",
        description="Runs F1DataAgent, IntelAgent, and FantasyContextAgent concurrently.",
        sub_agents=[
            _build_f1_data_agent(gateway, memory),
            _build_intel_agent(gateway, memory),
            _build_fantasy_context_agent(gateway, memory),
        ],
    )


def _build_submission_agent(gateway):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent("submission_agent", ["validate_team", "submit_team"])
    return LlmAgent(
        name="SubmissionAgent",
        model=LiteLlm(model=HAIKU),
        description="Validates and submits the recommended F1 Fantasy team.",
        instruction=(
            "Handle team submission. When asked to submit a team: "
            "1. Call validate_team with the proposed team composition. "
            "2. If validation passes, call submit_team. "
            "3. If validation fails, return the violations clearly. "
            "NEVER submit without validating first."
        ),
        tools=toolset or [],
    )


def build_f1_advisor_graph():
    """Build and return the complete F1 Fantasy Advisor agent graph."""
    try:
        from google.adk.agents import LlmAgent  # type: ignore
        from google.adk.models.lite_llm import LiteLlm  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "google-adk is required to build the F1 advisor agent. "
            "Install it with: pip install google-adk"
        ) from exc

    from app.agent.gateway import AgentCoreGateway
    from app.agent.memory import AgentCoreMemory

    gateway = AgentCoreGateway()
    memory = AgentCoreMemory()

    data_gathering = _build_data_gathering_agent(gateway, memory)
    submission_agent = _build_submission_agent(gateway)

    advisor = LlmAgent(
        name="F1FantasyAdvisor",
        model=LiteLlm(model=SONNET),
        description="Root F1 Fantasy Advisor — orchestrates data gathering and team recommendation.",
        instruction=ADVISOR_SYSTEM_PROMPT,
        sub_agents=[data_gathering, submission_agent],
    )

    logger.info("Built F1 Fantasy Advisor agent graph")
    return advisor
