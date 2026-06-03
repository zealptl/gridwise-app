"""Fantasy Tools — delegation wrappers and rule helpers."""

from app.agent.tools.f1_fantasy import (
    get_f1_fantasy_chips,
    get_f1_fantasy_prices,
    get_f1_fantasy_team,
)
from app.models.rule import Rule, RuleType


# ---------------------------------------------------------------------------
# 7.10  User team (delegation)
# ---------------------------------------------------------------------------

async def get_user_team(session_state: dict) -> dict:
    """Return the authenticated user's current F1 Fantasy team."""
    return await get_f1_fantasy_team(session_state)


# ---------------------------------------------------------------------------
# 7.11  Current prices (delegation)
# ---------------------------------------------------------------------------

async def get_current_prices() -> dict:
    """Return current driver and constructor prices."""
    return await get_f1_fantasy_prices()


# ---------------------------------------------------------------------------
# 7.12  Available chips (delegation)
# ---------------------------------------------------------------------------

async def get_available_chips(session_state: dict) -> dict:
    """Return available chips/boosters for the authenticated user."""
    return await get_f1_fantasy_chips(session_state)


# ---------------------------------------------------------------------------
# 7.15  Active rules
# ---------------------------------------------------------------------------

def _format_rule(rule: Rule) -> dict:
    """Convert a Rule document to a human-readable dict."""
    config: dict = rule.config or {}

    if rule.rule_type == RuleType.BUDGET_CAP:
        constraint = f"Total team cost must not exceed {config.get('max_budget', '?')}M"
    elif rule.rule_type == RuleType.ROSTER_SIZE:
        driver_count = config.get("driver_count", config.get("drivers", "?"))
        constructor_count = config.get("constructor_count", config.get("constructors", "?"))
        constraint = (
            f"Team must include exactly {driver_count} drivers "
            f"and {constructor_count} constructors"
        )
    else:
        constraint = str(config)

    return {
        "rule_type": rule.rule_type,
        "name": rule.name,
        "description": rule.description,
        "constraint": constraint,
    }


async def get_active_rules() -> dict:
    """
    Return all currently active rules from the database.

    Returns:
        {"rules": list[dict]}  — each dict has rule_type, name, description,
                                  and a human-readable constraint string.
    """
    rules = await Rule.find(Rule.is_active == True).to_list()  # noqa: E712
    return {"rules": [_format_rule(r) for r in rules]}
