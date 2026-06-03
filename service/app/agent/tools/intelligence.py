"""Intelligence Tools — WeatherAPI, The Odds API, and Reddit sentiment."""

import json
import os
from typing import Any

import boto3
import httpx

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

TIMEOUT = 10.0


# ---------------------------------------------------------------------------
# Secrets Manager helper
# ---------------------------------------------------------------------------

def _get_secret(secret_name: str) -> dict:
    """Retrieve a JSON secret from AWS Secrets Manager."""
    client = boto3.client("secretsmanager", region_name=AWS_REGION)
    resp = client.get_secret_value(SecretId=secret_name)
    return json.loads(resp["SecretString"])


# ---------------------------------------------------------------------------
# 7.3  Weather forecast
# ---------------------------------------------------------------------------

async def get_weather(circuit_location: str) -> dict:
    """
    Fetch a 3-day weather forecast for the given circuit location.

    API key is read from Secrets Manager secret ``gridwise/weather-api-key``
    (field ``value``).

    Returns:
        {
          "location": str,
          "forecast": list[dict],
          "race_day_forecast": dict,
        }

    On error returns {"error": "WeatherAPI unavailable"}.
    """
    try:
        secret = _get_secret("gridwise/weather-api-key")
        api_key: str = secret["value"]

        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {"q": circuit_location, "days": 3, "key": api_key}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        forecast_days: list[dict] = data.get("forecast", {}).get("forecastday", [])
        race_day_forecast: dict = forecast_days[-1] if forecast_days else {}

        return {
            "location": data.get("location", {}).get("name", circuit_location),
            "forecast": forecast_days,
            "race_day_forecast": race_day_forecast,
        }
    except Exception:
        return {"error": "WeatherAPI unavailable"}


# ---------------------------------------------------------------------------
# 7.4  Odds / implied probabilities
# ---------------------------------------------------------------------------

async def get_odds() -> dict:
    """
    Fetch Formula 1 betting odds and convert to implied probabilities.

    API key is read from Secrets Manager secret ``gridwise/odds-api-key``
    (field ``value``).

    Returns:
        {
          "event": str,
          "probabilities": dict[str, float],
        }

    On error returns {"error": "Odds API unavailable"}.
    """
    try:
        secret = _get_secret("gridwise/odds-api-key")
        api_key: str = secret["value"]

        url = (
            "https://api.the-odds-api.com/v4/sports/motorsport_formula_one/odds/"
        )
        params = {
            "apiKey": api_key,
            "regions": "uk",
            "markets": "h2h",
        }

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            events: list[dict] = resp.json()

        if not events:
            return {"event": "", "probabilities": {}}

        event = events[0]
        event_name: str = event.get("sport_title", "") + " — " + event.get(
            "commence_time", ""
        )

        probabilities: dict[str, float] = {}
        for bookmaker in event.get("bookmakers", []):
            for market in bookmaker.get("markets", []):
                if market.get("key") == "h2h":
                    for outcome in market.get("outcomes", []):
                        name: str = outcome.get("name", "")
                        decimal_odds: float = float(outcome.get("price", 1))
                        if decimal_odds > 0 and name not in probabilities:
                            probabilities[name] = round(1 / decimal_odds, 4)
                    break
            if probabilities:
                break

        return {"event": event_name, "probabilities": probabilities}
    except Exception:
        return {"error": "Odds API unavailable"}


# ---------------------------------------------------------------------------
# 7.5  Reddit sentiment
# ---------------------------------------------------------------------------

async def get_reddit_sentiment(race_name: str) -> dict:
    """
    Fetch recent Reddit posts mentioning ``race_name`` from r/formula1 and
    r/FantasyF1, then produce a basic sentiment summary.

    Credentials are read from Secrets Manager secret
    ``gridwise/reddit-credentials`` (fields ``client_id``, ``client_secret``).

    Returns:
        {
          "r_formula1": list[dict],
          "r_FantasyF1": list[dict],
          "sentiment_summary": str,
        }

    On error returns {"error": "Reddit API unavailable"}.
    """
    try:
        secret = _get_secret("gridwise/reddit-credentials")
        client_id: str = secret["client_id"]
        client_secret: str = secret["client_secret"]

        # OAuth2 client-credentials flow
        token_url = "https://www.reddit.com/api/v1/access_token"
        headers = {"User-Agent": "GridWise/1.0 (F1 AI Advisor)"}

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            token_resp = await client.post(
                token_url,
                data={"grant_type": "client_credentials"},
                auth=(client_id, client_secret),
                headers=headers,
            )
            token_resp.raise_for_status()
            access_token: str = token_resp.json()["access_token"]

            auth_headers = {
                **headers,
                "Authorization": f"Bearer {access_token}",
            }

            async def _search_subreddit(subreddit: str) -> list[dict]:
                search_url = (
                    f"https://oauth.reddit.com/r/{subreddit}/search"
                )
                params = {
                    "q": race_name,
                    "restrict_sr": "true",
                    "sort": "new",
                    "limit": 25,
                }
                r = await client.get(
                    search_url, params=params, headers=auth_headers
                )
                r.raise_for_status()
                posts_raw: list[Any] = (
                    r.json().get("data", {}).get("children", [])
                )
                return [
                    {
                        "title": p["data"].get("title", ""),
                        "score": p["data"].get("score", 0),
                        "url": p["data"].get("url", ""),
                        "created_utc": p["data"].get("created_utc", 0),
                    }
                    for p in posts_raw
                ]

            formula1_posts = await _search_subreddit("formula1")
            fantasy_posts = await _search_subreddit("FantasyF1")

        total = len(formula1_posts) + len(fantasy_posts)
        sentiment_summary = (
            f"Found {total} posts mentioning '{race_name}' "
            f"({len(formula1_posts)} in r/formula1, "
            f"{len(fantasy_posts)} in r/FantasyF1)."
        )

        return {
            "r_formula1": formula1_posts,
            "r_FantasyF1": fantasy_posts,
            "sentiment_summary": sentiment_summary,
        }
    except Exception:
        return {"error": "Reddit API unavailable"}
