"""F1 Data Tools — OpenF1 (live session) and Jolpica/Ergast (historical) API clients."""

import httpx

OPENF1_BASE = "https://api.openf1.org/v1"
JOLPICA_BASE = "https://api.jolpi.ca/ergast/f1"

TIMEOUT = 10.0


async def get_live_session_data() -> dict:
    """
    Fetch live session data from the OpenF1 API for the latest session.

    Returns a structured dict with keys:
      session, laps, stints, weather, race_control

    On any error returns {"error": "OpenF1 API unavailable", "available": False}.
    """
    endpoints = {
        "session": f"{OPENF1_BASE}/sessions?session_key=latest",
        "laps": f"{OPENF1_BASE}/laps?session_key=latest",
        "stints": f"{OPENF1_BASE}/stints?session_key=latest",
        "weather": f"{OPENF1_BASE}/weather?session_key=latest",
        "race_control": f"{OPENF1_BASE}/race_control?session_key=latest",
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            result: dict = {}
            for key, url in endpoints.items():
                resp = await client.get(url)
                resp.raise_for_status()
                result[key] = resp.json()
            return result
    except Exception:
        return {"error": "OpenF1 API unavailable", "available": False}


async def get_historical_performance() -> dict:
    """
    Fetch historical performance data from the Jolpica/Ergast API.

    Returns a structured dict with keys:
      driver_standings, constructor_standings, recent_results

    On partial failure, failed endpoints contain {"error": "..."} instead of data.
    """
    endpoints = {
        "driver_standings": f"{JOLPICA_BASE}/current/driverStandings.json",
        "constructor_standings": f"{JOLPICA_BASE}/current/constructorStandings.json",
        "recent_results": f"{JOLPICA_BASE}/current/next/results.json",
    }

    result: dict = {}

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        for key, url in endpoints.items():
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                result[key] = resp.json()
            except Exception as exc:
                result[key] = {"error": str(exc)}

    return result
