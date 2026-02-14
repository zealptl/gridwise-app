"""Tests for Roster Size Rule"""

import pytest

from app.models.rule import Rule, RuleSeverity, RuleType, ValidationLogic
from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam
from app.services.rules.roster_size_rule import RosterSizeRule


@pytest.mark.asyncio
async def test_roster_size_drivers_passes():
    """Test roster size rule passes with correct number of drivers"""
    rule = Rule(
        rule_type=RuleType.ROSTER_SIZE,
        name="Driver Roster Size",
        description="Must have 5 drivers",
        config={"required_drivers": 5},
        validation_logic=ValidationLogic(
            operator="==",
            field="len(drivers)",
            threshold="config.required_drivers",
            error_message_template="Invalid driver count: {actual} drivers (required: {required})",
        ),
        severity=RuleSeverity.ERROR,
        is_active=True,
        applies_to="team",
    )

    validator = RosterSizeRule(rule)

    # Create team with 5 drivers
    team = FantasyTeam(
        team_name="Test Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=10.0)
            for i in range(5)
        ],
    )

    violation = await validator.runRule(team)

    assert violation is None


@pytest.mark.asyncio
async def test_roster_size_drivers_fails():
    """Test roster size rule fails with wrong number of drivers"""
    rule = Rule(
        rule_type=RuleType.ROSTER_SIZE,
        name="Driver Roster Size",
        description="Must have 5 drivers",
        config={"required_drivers": 5},
        validation_logic=ValidationLogic(
            operator="==",
            field="len(drivers)",
            threshold="config.required_drivers",
            error_message_template="Invalid driver count: {actual} drivers (required: {required})",
        ),
        severity=RuleSeverity.ERROR,
        is_active=True,
        applies_to="team",
    )

    validator = RosterSizeRule(rule)

    # Create team with 3 drivers
    team = FantasyTeam(
        team_name="Test Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=10.0)
            for i in range(3)
        ],
    )

    violation = await validator.runRule(team)

    assert violation is not None
    assert violation.severity == "error"
    assert violation.details["actual_drivers"] == 3
    assert violation.details["required_drivers"] == 5


@pytest.mark.asyncio
async def test_roster_size_constructors_passes():
    """Test roster size rule passes with correct number of constructors"""
    rule = Rule(
        rule_type=RuleType.ROSTER_SIZE,
        name="Constructor Roster Size",
        description="Must have 2 constructors",
        config={"required_constructors": 2},
        validation_logic=ValidationLogic(
            operator="==",
            field="len(constructors)",
            threshold="config.required_constructors",
            error_message_template="Invalid constructor count: {actual} constructors (required: {required})",
        ),
        severity=RuleSeverity.ERROR,
        is_active=True,
        applies_to="team",
    )

    validator = RosterSizeRule(rule)

    # Create team with 2 constructors
    team = FantasyTeam(
        team_name="Test Team",
        created_by="test_user",
        constructors=[
            ConstructorSelection(constructor_id=f"c{i}", constructor_name=f"Constructor {i}", price=20.0)
            for i in range(2)
        ],
    )

    violation = await validator.runRule(team)

    assert violation is None
