"""
Agent tool endpoints — one POST per tool, called by AgentCore Gateway.
All routes require IAM SigV4 authentication.
"""
import logging
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent/tools", tags=["agent-tools"])


# ---------------------------------------------------------------------------
# IAM SigV4 auth dependency
# ---------------------------------------------------------------------------

async def verify_iam_sigv4(authorization: Optional[str] = Header(default=None)) -> None:
    """Reject requests that don't carry an AWS SigV4 Authorization header."""
    if not authorization or not authorization.startswith("AWS4-HMAC-SHA256"):
        raise HTTPException(status_code=403, detail="IAM SigV4 authentication required")


# ---------------------------------------------------------------------------
# Request bodies
# ---------------------------------------------------------------------------

class EmptyBody(BaseModel):
    pass


class CircuitLocationBody(BaseModel):
    circuit_location: str


class RaceNameBody(BaseModel):
    race_name: str


class SessionStateBody(BaseModel):
    session_state: dict = {}


class ValidateTeamBody(BaseModel):
    team: dict
    user_team_count: int = 0


class SubmitTeamBody(BaseModel):
    session_state: dict = {}
    team: dict
    validated: bool = False


# ---------------------------------------------------------------------------
# F1 data tools
# ---------------------------------------------------------------------------

@router.post("/get-live-session-data", dependencies=[Depends(verify_iam_sigv4)])
async def get_live_session_data_endpoint() -> Any:
    from app.agent.tools.f1_data import get_live_session_data
    return await get_live_session_data()


@router.post("/get-historical-performance", dependencies=[Depends(verify_iam_sigv4)])
async def get_historical_performance_endpoint() -> Any:
    from app.agent.tools.f1_data import get_historical_performance
    return await get_historical_performance()


# ---------------------------------------------------------------------------
# Intelligence tools (premium)
# ---------------------------------------------------------------------------

@router.post("/get-weather", dependencies=[Depends(verify_iam_sigv4)])
async def get_weather_endpoint(body: CircuitLocationBody) -> Any:
    from app.agent.tools.intelligence import get_weather
    return await get_weather(body.circuit_location)


@router.post("/get-odds", dependencies=[Depends(verify_iam_sigv4)])
async def get_odds_endpoint() -> Any:
    from app.agent.tools.intelligence import get_odds
    return await get_odds()


@router.post("/get-reddit-sentiment", dependencies=[Depends(verify_iam_sigv4)])
async def get_reddit_sentiment_endpoint(body: RaceNameBody) -> Any:
    from app.agent.tools.intelligence import get_reddit_sentiment
    return await get_reddit_sentiment(body.race_name)


# ---------------------------------------------------------------------------
# Fantasy context tools
# ---------------------------------------------------------------------------

@router.post("/get-user-team", dependencies=[Depends(verify_iam_sigv4)])
async def get_user_team_endpoint(body: SessionStateBody) -> Any:
    from app.agent.tools.fantasy import get_user_team
    return await get_user_team(body.session_state)


@router.post("/get-current-prices", dependencies=[Depends(verify_iam_sigv4)])
async def get_current_prices_endpoint() -> Any:
    from app.agent.tools.fantasy import get_current_prices
    return await get_current_prices()


@router.post("/get-available-chips", dependencies=[Depends(verify_iam_sigv4)])
async def get_available_chips_endpoint(body: SessionStateBody) -> Any:
    from app.agent.tools.fantasy import get_available_chips
    return await get_available_chips(body.session_state)


@router.post("/get-active-rules", dependencies=[Depends(verify_iam_sigv4)])
async def get_active_rules_endpoint() -> Any:
    from app.agent.tools.fantasy import get_active_rules
    return await get_active_rules()


# ---------------------------------------------------------------------------
# Submission tools
# ---------------------------------------------------------------------------

@router.post("/validate-team", dependencies=[Depends(verify_iam_sigv4)])
async def validate_team_endpoint(body: ValidateTeamBody) -> Any:
    from app.agent.tools.submission import validate_team
    return await validate_team(body.team, body.user_team_count)


@router.post("/submit-team", dependencies=[Depends(verify_iam_sigv4)])
async def submit_team_endpoint(body: SubmitTeamBody) -> Any:
    if not body.validated:
        raise HTTPException(status_code=422, detail="Team must be validated before submission")
    from app.agent.tools.submission import submit_team
    return await submit_team(body.session_state, body.team)
