"""Tests for Rule Engine"""

import pytest

from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam
from app.models.validation import ValidationStatus
from app.services.rule_engine import RuleEngine


@pytest.mark.asyncio
async def test_rule_engine_loads_rules():
    """Test that rule engine loads active rules from database"""
    engine = RuleEngine()

    await engine.load_rules()

    # Should load the 7 rules we seeded
    assert len(engine.rules) == 7

    # Get loaded rules info
    rules_info = engine.get_loaded_rules()
    assert len(rules_info) == 7


@pytest.mark.asyncio
async def test_rule_engine_validates_valid_team():
    """Test rule engine validates a valid team"""
    engine = RuleEngine()
    await engine.load_rules()

    # Create a valid team
    team = FantasyTeam(
        team_name="Valid Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=15.0)
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(constructor_id=f"c{i}", constructor_name=f"Constructor {i}", price=12.5)
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
    )

    result = await engine.validate_team(team)

    # Team should be valid (budget: 75 + 25 = 100M, 5 drivers, 2 constructors, DRS assigned)
    assert result.is_valid
    assert result.status == ValidationStatus.VALID
    assert len(result.violations) == 0


@pytest.mark.asyncio
async def test_rule_engine_validates_invalid_team_budget():
    """Test rule engine detects budget cap violation"""
    engine = RuleEngine()
    await engine.load_rules()

    # Create team over budget
    team = FantasyTeam(
        team_name="Over Budget Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=25.0)
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(constructor_id=f"c{i}", constructor_name=f"Constructor {i}", price=20.0)
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
    )

    result = await engine.validate_team(team)

    # Should have budget violation (165M > 100M)
    assert not result.is_valid
    assert result.status == ValidationStatus.INVALID
    assert len(result.violations) > 0

    # Check for budget cap violation
    budget_violations = [v for v in result.violations if v.rule_type == "budget_cap"]
    assert len(budget_violations) == 1


@pytest.mark.asyncio
async def test_rule_engine_validates_invalid_team_roster():
    """Test rule engine detects roster size violations"""
    engine = RuleEngine()
    await engine.load_rules()

    # Create team with wrong roster size
    team = FantasyTeam(
        team_name="Wrong Roster Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=10.0)
            for i in range(3)  # Only 3 drivers instead of 5
        ],
        constructors=[
            ConstructorSelection(constructor_id=f"c{i}", constructor_name=f"Constructor {i}", price=10.0)
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
    )

    result = await engine.validate_team(team)

    # Should have roster size violation
    assert not result.is_valid
    assert result.status == ValidationStatus.INVALID

    # Check for roster size violation
    roster_violations = [v for v in result.violations if v.rule_type == "roster_size"]
    assert len(roster_violations) >= 1


@pytest.mark.asyncio
async def test_rule_engine_quick_validation():
    """Test quick validation method"""
    engine = RuleEngine()
    await engine.load_rules()

    # Valid team
    valid_team = FantasyTeam(
        team_name="Valid Team",
        created_by="test_user",
        drivers=[
            DriverSelection(driver_id=f"d{i}", driver_name=f"Driver {i}", team_name="Team", price=15.0)
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(constructor_id=f"c{i}", constructor_name=f"Constructor {i}", price=12.5)
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
    )

    is_valid = await engine.validate_team_quick(valid_team)
    assert is_valid

    # Invalid team
    invalid_team = FantasyTeam(
        team_name="Invalid Team",
        created_by="test_user",
        drivers=[],  # No drivers
        constructors=[],
    )

    is_valid = await engine.validate_team_quick(invalid_team)
    assert not is_valid
