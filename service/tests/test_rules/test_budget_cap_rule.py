"""Tests for Budget Cap Rule"""

import pytest

from app.models.rule import Rule, RuleSeverity, RuleType, ValidationLogic
from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam
from app.services.rules.budget_cap_rule import BudgetCapRule


@pytest.mark.asyncio
async def test_budget_cap_rule_passes():
    """Test budget cap rule passes when under limit"""
    # Create rule configuration
    rule = Rule(
        rule_type=RuleType.BUDGET_CAP,
        name="Budget Cap",
        description="Budget must not exceed 100M",
        config={"max_budget": 100.0},
        validation_logic=ValidationLogic(
            operator="<=",
            field="budget_used",
            threshold="config.max_budget",
            error_message_template="Budget exceeded: {budget_used}M / {max_budget}M",
        ),
        severity=RuleSeverity.ERROR,
        is_active=True,
        applies_to="team",
    )

    validator = BudgetCapRule(rule)

    # Create team with budget under cap
    team = FantasyTeam(
        team_name="Test Team",
        created_by="test_user",
        drivers=[
            DriverSelection(
                driver_id="d1",
                driver_name="Driver 1",
                team_name="Team A",
                price=20.0,
            ),
            DriverSelection(
                driver_id="d2",
                driver_name="Driver 2",
                team_name="Team B",
                price=15.0,
            ),
        ],
        constructors=[
            ConstructorSelection(
                constructor_id="c1",
                constructor_name="Constructor 1",
                price=25.0,
            ),
        ],
    )

    violation = await validator.runRule(team)

    assert violation is None
    assert team.budget_used == 60.0  # 20 + 15 + 25


@pytest.mark.asyncio
async def test_budget_cap_rule_fails():
    """Test budget cap rule fails when over limit"""
    rule = Rule(
        rule_type=RuleType.BUDGET_CAP,
        name="Budget Cap",
        description="Budget must not exceed 100M",
        config={"max_budget": 100.0},
        validation_logic=ValidationLogic(
            operator="<=",
            field="budget_used",
            threshold="config.max_budget",
            error_message_template="Budget exceeded: {budget_used}M / {max_budget}M",
        ),
        severity=RuleSeverity.ERROR,
        is_active=True,
        applies_to="team",
    )

    validator = BudgetCapRule(rule)

    # Create team with budget over cap
    team = FantasyTeam(
        team_name="Test Team",
        created_by="test_user",
        drivers=[
            DriverSelection(
                driver_id="d1",
                driver_name="Driver 1",
                team_name="Team A",
                price=50.0,
            ),
            DriverSelection(
                driver_id="d2",
                driver_name="Driver 2",
                team_name="Team B",
                price=40.0,
            ),
        ],
        constructors=[
            ConstructorSelection(
                constructor_id="c1",
                constructor_name="Constructor 1",
                price=15.0,
            ),
        ],
    )

    violation = await validator.runRule(team)

    assert violation is not None
    assert violation.severity == "error"
    assert violation.rule_type == "budget_cap"
    assert "Budget exceeded" in violation.message
    assert violation.details["budget_used"] == 105.0
    assert violation.details["overage"] == 5.0
