"""Unit tests for TeamService"""

import pytest
from fastapi import HTTPException

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.rule import Rule, RuleType, RuleSeverity, ValidationLogic
from app.services.team_service import TeamService


@pytest.fixture
async def seed_basic_data():
    """Seed basic drivers, constructors, and rules for testing"""
    # Clear existing data
    await Driver.delete_all()
    await Constructor.delete_all()
    await Rule.delete_all()

    # Create budget-friendly drivers
    drivers = [
        Driver(
            first_name="George",
            last_name="Russell",
            team_name="Mercedes",
            nationality="British",
            driver_number=63,
            price=8.0,
            status="active",
        ),
        Driver(
            first_name="Oscar",
            last_name="Piastri",
            team_name="McLaren",
            nationality="Australian",
            driver_number=81,
            price=8.5,
            status="active",
        ),
        Driver(
            first_name="Yuki",
            last_name="Tsunoda",
            team_name="RB",
            nationality="Japanese",
            driver_number=22,
            price=7.0,
            status="active",
        ),
        Driver(
            first_name="Lance",
            last_name="Stroll",
            team_name="Aston Martin",
            nationality="Canadian",
            driver_number=18,
            price=7.5,
            status="active",
        ),
        Driver(
            first_name="Pierre",
            last_name="Gasly",
            team_name="Alpine",
            nationality="French",
            driver_number=10,
            price=7.0,
            status="active",
        ),
    ]

    for driver in drivers:
        await driver.insert()

    # Create budget-friendly constructors
    constructors = [
        Constructor(
            name="Haas",
            full_name="MoneyGram Haas F1 Team",
            nationality="American",
            price=6.0,
            status="active",
        ),
        Constructor(
            name="Sauber",
            full_name="Stake F1 Team Kick Sauber",
            nationality="Swiss",
            price=5.5,
            status="active",
        ),
    ]

    for constructor in constructors:
        await constructor.insert()

    # Create basic rules
    rules = [
        Rule(
            rule_type=RuleType.BUDGET_CAP,
            name="Budget Cap Rule",
            description="Total team cost cannot exceed 100.0M",
            severity=RuleSeverity.ERROR,
            is_active=True,
            applies_to="team",
            config={"max_budget": 100.0},
            validation_logic=ValidationLogic(
                operator="<=",
                field="budget_used",
                threshold="config.max_budget",
                error_message_template="Budget exceeded: {budget_used}M / {max_budget}M",
            ),
        ),
        Rule(
            rule_type=RuleType.ROSTER_SIZE,
            name="Roster Size Rule",
            description="Must have exactly 5 drivers and 2 constructors",
            severity=RuleSeverity.ERROR,
            is_active=True,
            applies_to="team",
            config={"required_drivers": 5, "required_constructors": 2},
            validation_logic=ValidationLogic(
                operator="==",
                field="len(drivers)",
                threshold="config.required_drivers",
                error_message_template="Must have exactly {required_drivers} drivers",
            ),
        ),
        Rule(
            rule_type=RuleType.DRS_BOOST_REQUIRED,
            name="DRS Boost Rule",
            description="Must assign DRS Boost to exactly 1 driver",
            severity=RuleSeverity.ERROR,
            is_active=True,
            applies_to="team",
            config={},
            validation_logic=ValidationLogic(
                operator="custom",
                field="drs_boost_driver_id",
                threshold="",
                error_message_template="DRS Boost must be assigned to exactly 1 driver",
                function="validate_drs_boost",
            ),
        ),
    ]

    for rule in rules:
        await rule.insert()

    # Return driver and constructor IDs for easy access
    driver_ids = [d.driver_id for d in drivers]
    constructor_ids = [c.constructor_id for c in constructors]

    return {"driver_ids": driver_ids, "constructor_ids": constructor_ids}


@pytest.mark.asyncio
async def test_create_valid_team(seed_basic_data):
    """Test creating a valid team passes validation"""
    service = TeamService()
    data = seed_basic_data

    team = await service.create_team(
        team_name="Test Team",
        driver_ids=data["driver_ids"],
        constructor_ids=data["constructor_ids"],
        drs_boost_driver_id=data["driver_ids"][0],
        created_by="test-user",
        season=2026,
    )

    assert team is not None
    assert team.is_valid
    assert team.team_name == "Test Team"
    assert len(team.drivers) == 5
    assert len(team.constructors) == 2
    assert team.drs_boost_driver_id == data["driver_ids"][0]
    assert team.budget_used <= 100.0
    assert team.budget_remaining >= 0


@pytest.mark.asyncio
async def test_create_team_driver_not_found(seed_basic_data):
    """Test creating team with non-existent driver fails"""
    service = TeamService()
    data = seed_basic_data

    # Use a non-existent driver ID
    invalid_driver_ids = data["driver_ids"][:4] + ["non-existent-driver-id"]

    with pytest.raises(HTTPException) as exc:
        await service.create_team(
            team_name="Invalid Team",
            driver_ids=invalid_driver_ids,
            constructor_ids=data["constructor_ids"],
            drs_boost_driver_id=invalid_driver_ids[0],
            created_by="test-user",
            season=2026,
        )

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_create_team_constructor_not_found(seed_basic_data):
    """Test creating team with non-existent constructor fails"""
    service = TeamService()
    data = seed_basic_data

    # Use a non-existent constructor ID
    invalid_constructor_ids = [data["constructor_ids"][0], "non-existent-constructor"]

    with pytest.raises(HTTPException) as exc:
        await service.create_team(
            team_name="Invalid Team",
            driver_ids=data["driver_ids"],
            constructor_ids=invalid_constructor_ids,
            drs_boost_driver_id=data["driver_ids"][0],
            created_by="test-user",
            season=2026,
        )

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_create_team_inactive_driver(seed_basic_data):
    """Test creating team with inactive driver fails"""
    service = TeamService()
    data = seed_basic_data

    # Mark first driver as inactive
    driver = await Driver.find_one(Driver.driver_id == data["driver_ids"][0])
    driver.status = "inactive"
    await driver.save()

    with pytest.raises(HTTPException) as exc:
        await service.create_team(
            team_name="Invalid Team",
            driver_ids=data["driver_ids"],
            constructor_ids=data["constructor_ids"],
            drs_boost_driver_id=data["driver_ids"][0],
            created_by="test-user",
            season=2026,
        )

    assert exc.value.status_code == 400
    assert "not active" in exc.value.detail.lower()


@pytest.mark.asyncio
async def test_budget_calculation(seed_basic_data):
    """Test budget is calculated correctly"""
    service = TeamService()
    data = seed_basic_data

    team = await service.create_team(
        team_name="Budget Test Team",
        driver_ids=data["driver_ids"],
        constructor_ids=data["constructor_ids"],
        drs_boost_driver_id=data["driver_ids"][0],
        created_by="test-user",
        season=2026,
    )

    # Calculate expected budget
    expected_drivers = 8.0 + 8.5 + 7.0 + 7.5 + 7.0  # 38.0
    expected_constructors = 6.0 + 5.5  # 11.5
    expected_total = expected_drivers + expected_constructors  # 49.5

    assert team.budget_used == expected_total
    assert team.budget_remaining == 100.0 - expected_total
    assert team.budget_cap == 100.0
