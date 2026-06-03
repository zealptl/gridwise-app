"""F1 Fantasy API Tools — auth, prices, team, and chips."""

import json
import os

import boto3
import httpx

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TIMEOUT = 15.0

# Public partner API key (not a secret — provided by F1 Fantasy partner programme)
F1_FANTASY_API_KEY = "fCUCjWrKPu9ylJwRAv8BpGLEgiAuThx7"

F1_FANTASY_BASE = "https://fantasy-api.formula1.com/partner_games/f1"
F1_AUTH_URL = (
    "https://api.formula1.com/v2/account/subscriber/authenticate/by-password"
)


# ---------------------------------------------------------------------------
# Secrets Manager helper
# ---------------------------------------------------------------------------

def _get_secret(secret_name: str) -> dict:
    """Retrieve a JSON secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=secret_name)
    return json.loads(resp["SecretString"])


# ---------------------------------------------------------------------------
# 7.6  Authenticate
# ---------------------------------------------------------------------------

async def authenticate_f1_fantasy(session_state: dict) -> str:
    """
    Obtain (or return a cached) F1 Fantasy session token.

    Checks ``session_state["f1_session_token"]`` first.  If absent,
    authenticates using credentials from Secrets Manager secret
    ``gridwise/f1-credentials`` (fields ``username``, ``password``).

    Stores the retrieved ``SessionId`` back into ``session_state``.

    Raises:
        RuntimeError: If authentication fails for any reason.
    """
    cached = session_state.get("f1_session_token")
    if cached:
        return cached

    try:
        creds = _get_secret("gridwise/f1-credentials")
        username: str = creds["username"]
        password: str = creds["password"]
    except Exception as exc:
        raise RuntimeError("F1 Fantasy auth failed") from exc

    payload = {
        "DistributionChannel": "d861e38f-05ea-4063-8776-a7e2b6d885a7",
        "Login": username,
        "Password": password,
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.post(F1_AUTH_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        session_id: str = data["SessionId"]
        session_state["f1_session_token"] = session_id
        return session_id
    except Exception as exc:
        raise RuntimeError("F1 Fantasy auth failed") from exc


# ---------------------------------------------------------------------------
# 7.7  Prices (public endpoints)
# ---------------------------------------------------------------------------

async def get_f1_fantasy_prices() -> dict:
    """
    Fetch current driver and constructor prices from the F1 Fantasy API.

    Uses the public partner API key — no authentication required.

    Returns:
        {
          "drivers": list[dict],        # id, name, price, team
          "constructors": list[dict],   # id, name, price, team
        }
    """
    headers = {"apikey": F1_FANTASY_API_KEY}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        players_resp = await client.get(
            f"{F1_FANTASY_BASE}/players", headers=headers
        )
        players_resp.raise_for_status()

        teams_resp = await client.get(
            f"{F1_FANTASY_BASE}/teams", headers=headers
        )
        teams_resp.raise_for_status()

    def _normalise_player(p: dict) -> dict:
        return {
            "id": p.get("id", ""),
            "name": p.get("display_name") or f"{p.get('first_name', '')} {p.get('last_name', '')}".strip(),
            "price": p.get("price", 0.0),
            "team": p.get("team_name") or p.get("team", ""),
        }

    def _normalise_team(t: dict) -> dict:
        return {
            "id": t.get("id", ""),
            "name": t.get("name", ""),
            "price": t.get("price", 0.0),
            "team": t.get("name", ""),
        }

    raw_players: list = players_resp.json() if isinstance(players_resp.json(), list) else players_resp.json().get("players", [])
    raw_teams: list = teams_resp.json() if isinstance(teams_resp.json(), list) else teams_resp.json().get("teams", [])

    return {
        "drivers": [_normalise_player(p) for p in raw_players],
        "constructors": [_normalise_team(t) for t in raw_teams],
    }


# ---------------------------------------------------------------------------
# 7.8  User team
# ---------------------------------------------------------------------------

async def get_f1_fantasy_team(session_state: dict) -> dict:
    """
    Fetch the authenticated user's current F1 Fantasy team.

    Returns:
        {
          "team": dict,
          "budget_remaining": float,
          "transfer_count": int,
        }
    """
    token = await authenticate_f1_fantasy(session_state)

    url = f"{F1_FANTASY_BASE}/picked_teams"
    params = {"my_current_picked_teams": "true"}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        # Try Authorization header first, fall back to Cookie
        for attempt_headers in [
            {"Authorization": f"Bearer {token}"},
            {"Cookie": f"sessionId={token}"},
        ]:
            resp = await client.get(url, params=params, headers=attempt_headers)
            if resp.status_code == 200:
                break
        resp.raise_for_status()

    data: dict = resp.json()
    team_data: dict = data.get("picked_team") or data.get("team") or data
    budget_remaining: float = float(
        data.get("budget_remaining") or data.get("remaining_budget") or 0.0
    )
    transfer_count: int = int(
        data.get("transfer_count") or data.get("transfers_used") or 0
    )

    return {
        "team": team_data,
        "budget_remaining": budget_remaining,
        "transfer_count": transfer_count,
    }


# ---------------------------------------------------------------------------
# 7.9  Available chips / boosters
# ---------------------------------------------------------------------------

async def get_f1_fantasy_chips(session_state: dict) -> dict:
    """
    Fetch available chips/boosters for the authenticated user.

    Returns:
        {
          "available_chips": list[dict],   # name, available, used
        }
    """
    token = await authenticate_f1_fantasy(session_state)

    url = f"{F1_FANTASY_BASE}/boosters"

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for attempt_headers in [
            {"Authorization": f"Bearer {token}"},
            {"Cookie": f"sessionId={token}"},
        ]:
            resp = await client.get(url, headers=attempt_headers)
            if resp.status_code == 200:
                break
        resp.raise_for_status()

    raw: list = resp.json() if isinstance(resp.json(), list) else resp.json().get("boosters", [])

    chips = [
        {
            "name": chip.get("name") or chip.get("booster_name", ""),
            "available": bool(chip.get("available", False)),
            "used": bool(chip.get("used", False)),
        }
        for chip in raw
    ]

    return {"available_chips": chips}
