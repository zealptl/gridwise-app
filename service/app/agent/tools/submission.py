"""Submission Tools — team validation and submission."""

from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam
from app.services.rule_engine import RuleEngine
from app.services.team_service import TeamService


# ---------------------------------------------------------------------------
# 7.13  Validate team
# ---------------------------------------------------------------------------

async def validate_team(team: dict, user_team_count: int = 0) -> dict:
    """
    Validate a team dict against all active rules.

    ``team`` is expected to contain:
      - ``team_name`` (str)
      - ``created_by`` (str) — user_id
      - ``drivers`` (list[dict]) — each with driver_id, driver_name, team_name, price
      - ``constructors`` (list[dict]) — each with constructor_id, constructor_name, price
      - ``drs_boost_driver_id`` (str, optional)
      - ``budget_cap`` (float, optional, default 100.0)

    Returns:
        {"valid": bool, "violations": list[dict]}
    """
    # Build a FantasyTeam instance from the raw dict so RuleEngine can consume it
    drivers = [
        DriverSelection(**d) if isinstance(d, dict) else d
        for d in team.get("drivers", [])
    ]
    constructors = [
        ConstructorSelection(**c) if isinstance(c, dict) else c
        for c in team.get("constructors", [])
    ]

    fantasy_team = FantasyTeam(
        team_name=team.get("team_name", ""),
        created_by=team.get("created_by", ""),
        season=team.get("season", 2026),
        drivers=drivers,
        constructors=constructors,
        drs_boost_driver_id=team.get("drs_boost_driver_id"),
        budget_cap=team.get("budget_cap", 100.0),
    )
    fantasy_team.calculate_budget()

    rule_engine = RuleEngine()
    await rule_engine.load_rules()

    result = await rule_engine.validate_team(
        fantasy_team, user_team_count=user_team_count
    )

    violations = [
        {
            "rule_name": v.rule_name,
            "message": v.message,
            "severity": v.severity,
            "details": v.details,
        }
        for v in result.violations
    ]

    return {"valid": result.is_valid, "violations": violations if not result.is_valid else []}


# ---------------------------------------------------------------------------
# 7.14  Submit team
# ---------------------------------------------------------------------------

async def submit_team(session_state: dict, team: dict) -> dict:
    """
    Create (or update) the user's fantasy team via TeamService.

    ``session_state`` must contain ``user_id``.

    ``team`` must contain:
      - ``team_name`` (str)
      - ``driver_ids`` (list[str])
      - ``constructor_ids`` (list[str])
      - ``drs_boost_driver_id`` (str)
      - ``season`` (int, optional, default 2026)

    Returns:
        {"success": True, "team_id": str}  or  {"error": str}
    """
    user_id: str = session_state.get("user_id", "")
    if not user_id:
        return {"error": "user_id not found in session state"}

    team_name: str = team.get("team_name", "")
    driver_ids: list = team.get("driver_ids", [])
    constructor_ids: list = team.get("constructor_ids", [])
    drs_boost_driver_id: str = team.get("drs_boost_driver_id", "")
    season: int = int(team.get("season", 2026))

    service = TeamService()

    # Check whether the user already has a team this season; if yes, update it.
    existing = await FantasyTeam.find_one(
        FantasyTeam.created_by == user_id,
        FantasyTeam.season == season,
        FantasyTeam.is_active == True,  # noqa: E712
    )

    if existing:
        result = await service.update_team(
            team_id=existing.team_id,
            new_driver_ids=driver_ids,
            new_constructor_ids=constructor_ids,
            new_drs_boost_driver_id=drs_boost_driver_id,
        )
    else:
        result = await service.create_team(
            team_name=team_name,
            driver_ids=driver_ids,
            constructor_ids=constructor_ids,
            drs_boost_driver_id=drs_boost_driver_id,
            created_by=user_id,
            season=season,
        )

    return {"success": True, "team_id": str(result.team_id)}
