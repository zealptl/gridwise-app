"""Integration tests for Team Creation API"""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.rule import Rule, RuleType, RuleSeverity, ValidationLogic
from app.models.team import FantasyTeam


@pytest.fixture
async def seed_test_data():
    """Seed drivers, constructors, and rules for testing"""
    # Clear existing data
    await Driver.delete_all()
    await Constructor.delete_all()
    await Rule.delete_all()
    await FantasyTeam.delete_all()

    # Create budget-friendly drivers (total ~38M)
    drivers_data = [
        {
            "first_name": "George",
            "last_name": "Russell",
            "team_name": "Mercedes",
            "nationality": "British",
            "driver_number": 63,
            "price": 8.0,
        },
        {
            "first_name": "Oscar",
            "last_name": "Piastri",
            "team_name": "McLaren",
            "nationality": "Australian",
            "driver_number": 81,
            "price": 8.5,
        },
        {
            "first_name": "Yuki",
            "last_name": "Tsunoda",
            "team_name": "RB",
            "nationality": "Japanese",
            "driver_number": 22,
            "price": 7.0,
        },
        {
            "first_name": "Lance",
            "last_name": "Stroll",
            "team_name": "Aston Martin",
            "nationality": "Canadian",
            "driver_number": 18,
            "price": 7.5,
        },
        {
            "first_name": "Pierre",
            "last_name": "Gasly",
            "team_name": "Alpine",
            "nationality": "French",
            "driver_number": 10,
            "price": 7.0,
        },
    ]

    # Create expensive drivers for budget test (total ~150M - will exceed budget)
    expensive_drivers_data = [
        {
            "first_name": "Max",
            "last_name": "Verstappen",
            "team_name": "Red Bull Racing",
            "nationality": "Dutch",
            "driver_number": 1,
            "price": 30.5,
        },
        {
            "first_name": "Charles",
            "last_name": "Leclerc",
            "team_name": "Ferrari",
            "nationality": "Monegasque",
            "driver_number": 16,
            "price": 29.0,
        },
        {
            "first_name": "Lewis",
            "last_name": "Hamilton",
            "team_name": "Mercedes",
            "nationality": "British",
            "driver_number": 44,
            "price": 28.0,
        },
        {
            "first_name": "Sergio",
            "last_name": "Perez",
            "team_name": "Red Bull Racing",
            "nationality": "Mexican",
            "driver_number": 11,
            "price": 26.0,
        },
        {
            "first_name": "Carlos",
            "last_name": "Sainz",
            "team_name": "Ferrari",
            "nationality": "Spanish",
            "driver_number": 55,
            "price": 25.5,
        },
    ]

    all_drivers_data = drivers_data + expensive_drivers_data
    driver_objects = []

    for driver_data in all_drivers_data:
        driver = Driver(**driver_data, status="active")
        await driver.insert()
        driver_objects.append(driver)

    # Create constructors
    constructors_data = [
        {
            "name": "Haas",
            "full_name": "MoneyGram Haas F1 Team",
            "nationality": "American",
            "price": 6.0,
        },
        {
            "name": "Sauber",
            "full_name": "Stake F1 Team Kick Sauber",
            "nationality": "Swiss",
            "price": 5.5,
        },
        {
            "name": "Red Bull",
            "full_name": "Oracle Red Bull Racing",
            "nationality": "Austrian",
            "price": 28.0,
        },
        {
            "name": "Ferrari",
            "full_name": "Scuderia Ferrari",
            "nationality": "Italian",
            "price": 26.5,
        },
    ]

    constructor_objects = []
    for constructor_data in constructors_data:
        constructor = Constructor(**constructor_data, status="active")
        await constructor.insert()
        constructor_objects.append(constructor)

    # Create rules
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

    return {
        "budget_drivers": [d.driver_id for d in driver_objects[:5]],
        "expensive_drivers": [d.driver_id for d in driver_objects[5:]],
        "budget_constructors": [c.constructor_id for c in constructor_objects[:2]],
        "expensive_constructors": [c.constructor_id for c in constructor_objects[2:]],
    }


@pytest.mark.asyncio
async def test_create_team_success(seed_test_data):
    """Test successful team creation"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "My Test Team",
                "driver_ids": data["budget_drivers"],
                "constructor_ids": data["budget_constructors"],
                "drs_boost_driver_id": data["budget_drivers"][0],
                "season": 2026,
            },
        )

        assert response.status_code == 201

        result = response.json()
        assert result["team_name"] == "My Test Team"
        assert result["is_valid"] is True
        assert len(result["drivers"]) == 5
        assert len(result["constructors"]) == 2
        assert result["drs_boost_driver_id"] == data["budget_drivers"][0]
        assert result["budget_used"] <= 100.0
        assert result["budget_remaining"] >= 0
        assert "team_id" in result
        assert "created_at" in result


@pytest.mark.asyncio
async def test_create_team_budget_exceeded(seed_test_data):
    """Test team creation fails when budget exceeded"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Too Expensive Team",
                "driver_ids": data["expensive_drivers"],
                "constructor_ids": data["expensive_constructors"],
                "drs_boost_driver_id": data["expensive_drivers"][0],
                "season": 2026,
            },
        )

        assert response.status_code == 422

        result = response.json()
        assert result["detail"]["code"] == "RULE_VIOLATION"
        assert "violations" in result["detail"]
        assert len(result["detail"]["violations"]) > 0

        # Check that budget violation is in the list
        violations = result["detail"]["violations"]
        budget_violation = next(
            (v for v in violations if "budget" in v["message"].lower()), None
        )
        assert budget_violation is not None


@pytest.mark.asyncio
async def test_create_team_wrong_driver_count(seed_test_data):
    """Test team creation fails with wrong number of drivers"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try with only 4 drivers
        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Invalid Team",
                "driver_ids": data["budget_drivers"][:4],  # Only 4 drivers
                "constructor_ids": data["budget_constructors"],
                "drs_boost_driver_id": data["budget_drivers"][0],
                "season": 2026,
            },
        )

        assert response.status_code == 422
        result = response.json()
        assert "detail" in result


@pytest.mark.asyncio
async def test_create_team_duplicate_drivers(seed_test_data):
    """Test team creation fails with duplicate drivers"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Use same driver ID multiple times
        duplicate_driver_ids = [data["budget_drivers"][0]] * 5

        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Duplicate Team",
                "driver_ids": duplicate_driver_ids,
                "constructor_ids": data["budget_constructors"],
                "drs_boost_driver_id": duplicate_driver_ids[0],
                "season": 2026,
            },
        )

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_team_invalid_drs_boost(seed_test_data):
    """Test team creation fails when DRS boost not assigned to selected driver"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Try to assign DRS boost to a driver not in the team
        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Invalid DRS Team",
                "driver_ids": data["budget_drivers"],
                "constructor_ids": data["budget_constructors"],
                "drs_boost_driver_id": data["expensive_drivers"][0],  # Not in team
                "season": 2026,
            },
        )

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_team_driver_not_found(seed_test_data):
    """Test team creation fails with non-existent driver"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        invalid_driver_ids = data["budget_drivers"][:4] + ["non-existent-id"]

        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Not Found Team",
                "driver_ids": invalid_driver_ids,
                "constructor_ids": data["budget_constructors"],
                "drs_boost_driver_id": invalid_driver_ids[0],
                "season": 2026,
            },
        )

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_team_constructor_not_found(seed_test_data):
    """Test team creation fails with non-existent constructor"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        invalid_constructor_ids = [
            data["budget_constructors"][0],
            "non-existent-constructor",
        ]

        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Not Found Team",
                "driver_ids": data["budget_drivers"],
                "constructor_ids": invalid_constructor_ids,
                "drs_boost_driver_id": data["budget_drivers"][0],
                "season": 2026,
            },
        )

        assert response.status_code == 404
