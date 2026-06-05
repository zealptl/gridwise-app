"""
F1 Fantasy Advisor agent graph.
Uses Google ADK with Claude via Bedrock (LiteLLM bridge).
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

HAIKU = "bedrock/us.anthropic.claude-haiku-4-5-20251001-v1:0"
SONNET = "bedrock/us.anthropic.claude-sonnet-4-5-20250929-v1:0"

ADVISOR_SYSTEM_PROMPT = """You are the GridWise F1 Fantasy Advisor — an expert AI assistant that helps users optimise their F1 Fantasy team.

ORCHESTRATION RULES:
1. When a user asks for a recommendation, FIRST delegate to DataGathering to collect all necessary data in parallel.
2. After DataGathering completes, read all three session memory keys: f1_data, intel, fantasy_context.
3. Synthesise a recommendation based on ALL gathered data.
4. Present your recommendation using the display_team_recommendation tool with structured data.
5. WAIT for the user to explicitly confirm before delegating to SubmissionAgent.
6. Only delegate to SubmissionAgent after receiving explicit user confirmation.

TOOL AVAILABILITY:
- Free-tier users have access to F1 data tools, fantasy context tools, and submission tools.
- Premium-tier users additionally have access to intelligence tools (weather, odds).
- If intel data is unavailable (free-tier user), state this and provide a recommendation with reduced confidence based on available data only.
- Never refuse to provide a recommendation solely because intelligence tools are unavailable.

RULE COMPLIANCE:
Before proposing any team, read the `rules` field from `fantasy_context` in session memory and verify every pick satisfies all active constraints — budget cap, roster shape, DRS boost requirement, and driver eligibility. Never propose a team that violates an active rule.

REASONING APPROACH:
- Lead with data: cite specific stats from f1_data and intel to justify every pick.
- Acknowledge missing data: if an API was unavailable, state this and reduce confidence accordingly.
- Be explicit about uncertainty: use phrases like "based on available data" or "with reduced confidence" when data is incomplete.

SUBMISSION CONSTRAINT:
NEVER call SubmissionAgent without explicit user confirmation. The user must actively choose to apply the recommendation.

MEMORY CONTEXT:
- Before each turn, <PAST_CONVERSATIONS> may be injected with relevant memories from prior sessions.
- Use these memories to personalise recommendations — reference past preferences and strategies.
- If <PAST_CONVERSATIONS> is empty, provide a recommendation without prior context.
- Free-tier users: intelligence tools (weather, odds) are unavailable. State this and reduce confidence.
- Premium-tier users: all 11 tools available.
"""


def _build_f1_data_agent(gateway):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent(
        "f1_data_agent",
        "live F1 session data and historical driver and constructor performance standings",
    )
    return LlmAgent(
        name="F1DataAgent",
        model=LiteLlm(model=HAIKU),
        description="Fetches live F1 session data and historical driver/constructor performance.",
        instruction=(
            "Gather F1 performance data using your available tools. "
            "Call get_live_session_data to fetch the latest session (lap times, stints, weather, race control). "
            "Call get_historical_performance for championship standings and recent race results. "
            "If get_live_session_data returns {'error': ..., 'available': false}, write that error to memory — do not abort. "
            "After gathering all available data, write results to session memory with key 'f1_data'. "
            "If an individual endpoint fails, include {'error': '...', 'available': false} under that sub-key. "
            "Return a structured JSON summary of what you collected."
        ),
        tools=toolset or [],
    )


def _build_intel_agent(gateway):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent(
        "intel_agent",
        "external race intelligence including weather forecast and betting odds",
    )
    return LlmAgent(
        name="IntelAgent",
        model=LiteLlm(model=HAIKU),
        description="Gathers external intelligence: weather and betting odds.",
        instruction=(
            "Gather external race intelligence using your available tools. "
            "If you have no tools (free-tier user), write {'available': false, 'reason': 'intelligence tools require premium tier'} "
            "to session memory under key 'intel' and return immediately — this is expected behaviour, not an error. "
            "If you have tools: call get_weather with the circuit location and get_odds for race winner probabilities. "
            "On individual API failure, include the error under that sub-key and continue. "
            "Write all results to session memory under key 'intel'. "
            "Return a structured JSON summary."
        ),
        tools=toolset or [],
    )


def _build_fantasy_context_agent(gateway):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent(
        "fantasy_context_agent",
        "user fantasy team, driver and constructor prices, chip availability, and active game rules",
    )
    return LlmAgent(
        name="FantasyContextAgent",
        model=LiteLlm(model=HAIKU),
        description="Loads the user's current fantasy team, live prices, chip availability, and active rules.",
        instruction=(
            "Load the user's full fantasy context using your available tools. "
            "Call get_user_team to retrieve their current picks (pass session_state with user_id). "
            "Call get_current_prices for live driver and constructor prices. "
            "Call get_available_chips to check which boosters are still usable this season. "
            "Call get_active_rules to fetch all active game constraints. "
            "For any unavailable field, write null with an 'error' sub-key rather than omitting it. "
            "Write results to session memory under key 'fantasy_context' with sub-keys: team, prices, chips, rules. "
            "Return a structured JSON summary."
        ),
        tools=toolset or [],
    )


def _build_data_gathering_agent(gateway):
    from google.adk.agents import ParallelAgent  # type: ignore

    return ParallelAgent(
        name="DataGathering",
        description="Runs F1DataAgent, IntelAgent, and FantasyContextAgent concurrently.",
        sub_agents=[
            _build_f1_data_agent(gateway),
            _build_intel_agent(gateway),
            _build_fantasy_context_agent(gateway),
        ],
    )


def _build_submission_agent(gateway):
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore

    toolset = gateway.get_toolset_for_agent(
        "submission_agent",
        "validate and submit F1 fantasy team to GridWise database",
    )
    return LlmAgent(
        name="SubmissionAgent",
        model=LiteLlm(model=HAIKU),
        description="Validates and submits the recommended F1 Fantasy team.",
        instruction=(
            "Handle team submission in two mandatory steps: "
            "1. ALWAYS call validate_team first with the full proposed team. "
            "   If validation fails, return the violations clearly — do NOT proceed to submission. "
            "2. Only call submit_team after validate_team returns valid: true. "
            "   Pass validated: true in the submit_team request body. "
            "On submission success, confirm the team_id. On failure, report the error. "
            "NEVER skip validation. NEVER call submit_team without a prior successful validation."
        ),
        tools=toolset or [],
    )


def build_f1_advisor_graph(user_jwt: Optional[str] = None, user_id: str = "anonymous"):
    """Build and return the complete F1 Fantasy Advisor agent graph.

    Args:
        user_jwt: Raw Cognito JWT string from the user's Authorization header.
            Forwarded to AgentCoreGateway so the gateway can apply tier-based
            tool filtering for this user.
        user_id: The authenticated user's ID, used to scope session and memory
            services.
    """
    try:
        from google.adk.agents import LlmAgent  # type: ignore
        from google.adk.models.lite_llm import LiteLlm  # type: ignore
    except ImportError as exc:
        raise ImportError(
            "google-adk is required to build the F1 advisor agent. "
            "Install it with: pip install google-adk"
        ) from exc

    try:
        from app.agent.memory import AgentCoreMemoryService  # noqa: F401
        from app.agent.memory import get_memory_service
        from app.agent.session import AgentCoreSessionService  # noqa: F401
        from app.agent.session import get_session_service
    except ImportError:
        def get_memory_service():
            return None

        def get_session_service():
            return None

    try:
        from google.adk.tools import preload_memory  # type: ignore
        memory_tools = [preload_memory]
    except ImportError:
        memory_tools = []

    from app.agent.gateway import AgentCoreGateway

    session_service = get_session_service()
    memory_svc = get_memory_service()

    async def _persist_session_callback(callback_context) -> None:
        try:
            session = callback_context.session
            if memory_svc and session:
                await memory_svc.add_session_to_memory(session)
        except Exception as exc:
            logger.warning("after_agent_callback: session persist failed: %s", exc)

    gateway = AgentCoreGateway(jwt=user_jwt)
    data_gathering = _build_data_gathering_agent(gateway)
    submission_agent = _build_submission_agent(gateway)

    advisor = LlmAgent(
        name="F1FantasyAdvisor",
        model=LiteLlm(model=SONNET),
        description="Root F1 Fantasy Advisor — orchestrates data gathering and team recommendation.",
        instruction=ADVISOR_SYSTEM_PROMPT,
        sub_agents=[data_gathering, submission_agent],
        tools=memory_tools,
        after_agent_callback=_persist_session_callback,
    )

    logger.info(
        "Built F1 Fantasy Advisor agent graph (jwt=%s, user_id=%s)",
        "present" if user_jwt else "absent",
        user_id,
    )
    return advisor, session_service, memory_svc
