"""Integration tests for Team Update API"""

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
        {
            "first_name": "Liam",
            "last_name": "Lawson",
            "team_name": "RB",
            "nationality": "New Zealander",
            "driver_number": 30,
            "price": 7.5,
        },
        {
            "first_name": "Alex",
            "last_name": "Albon",
            "team_name": "Williams",
            "nationality": "Thai",
            "driver_number": 23,
            "price": 7.0,
        },
        {
            "first_name": "Nico",
            "last_name": "Hulkenberg",
            "team_name": "Haas",
            "nationality": "German",
            "driver_number": 27,
            "price": 7.0,
        },
        {
            "first_name": "Valtteri",
            "last_name": "Bottas",
            "team_name": "Sauber",
            "nationality": "Finnish",
            "driver_number": 77,
            "price": 7.5,
        },
        {
            "first_name": "Zhou",
            "last_name": "Guanyu",
            "team_name": "Sauber",
            "nationality": "Chinese",
            "driver_number": 24,
            "price": 6.5,
        },
    ]

    # Create expensive drivers for budget test
    expensive_drivers_data = [
        {
            "first_name": "Max",
            "last_name": "Verstappen",
            "team_name": "Red Bull Racing",
            "nationality": "Dutch",
            "driver_number": 1,
            "price": 30.5,
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
            "name": "Alpine",
            "full_name": "BWT Alpine F1 Team",
            "nationality": "French",
            "price": 6.5,
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
        "budget_drivers": [d.driver_id for d in driver_objects[:10]],
        "expensive_drivers": [d.driver_id for d in driver_objects[10:]],
        "budget_constructors": [c.constructor_id for c in constructor_objects[:3]],
        "expensive_constructors": [c.constructor_id for c in constructor_objects[3:]],
    }


async def create_test_team(driver_ids, constructor_ids, drs_boost_driver_id):
    """Helper to create a team for testing updates"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/teams/",
            json={
                "team_name": "Test Team",
                "driver_ids": driver_ids,
                "constructor_ids": constructor_ids,
                "drs_boost_driver_id": drs_boost_driver_id,
                "season": 2026,
            },
        )
        assert response.status_code == 201
        return response.json()


@pytest.mark.asyncio
async def test_update_team_single_driver_swap_success(seed_test_data):
    """Test updating team with single driver swap"""
    data = seed_test_data

    # Create team with first 5 drivers
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: swap 5th driver for 6th driver
    new_drivers = initial_drivers[:4] + [data["budget_drivers"][5]]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["drivers"]) == 5
        assert len(result["transfer_history"]) == 1
        assert result["transfer_history"][0]["transfers_used"] == 1
        assert result["transfer_history"][0]["penalty_points"] == 0
        assert result["current_race_transfers"] == 1
        assert result["is_valid"] is True


@pytest.mark.asyncio
async def test_update_team_multiple_swaps_no_penalty(seed_test_data):
    """Test updating team with 2 driver swaps (within free transfer limit)"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: swap 2 drivers (within limit of 2 free transfers)
    new_drivers = initial_drivers[:3] + data["budget_drivers"][5:7]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["transfer_history"]) == 1
        assert result["transfer_history"][0]["transfers_used"] == 2
        assert result["transfer_history"][0]["penalty_points"] == 0
        assert result["current_race_transfers"] == 2


@pytest.mark.asyncio
async def test_update_team_three_transfers_with_penalty(seed_test_data):
    """Test updating team with 3 transfers (1 excess = 10 point penalty)"""
    data = seed_test_data

    # Create team with drivers [0,1,2,3,4]
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: swap 3 drivers
    # Keep drivers [0,1], remove [2,3,4], add [5,6,7]
    # This is 3 transfers (3 removed, 3 added)
    # With 10 budget drivers now available (0-9), this is possible
    new_drivers = [
        data["budget_drivers"][0],
        data["budget_drivers"][1],
        data["budget_drivers"][5],
        data["budget_drivers"][6],
        data["budget_drivers"][7],
    ]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["transfer_history"]) == 1
        assert result["transfer_history"][0]["transfers_used"] == 3
        assert result["transfer_history"][0]["penalty_points"] == 10
        assert result["current_race_transfers"] == 3


@pytest.mark.asyncio
async def test_update_drs_boost_only_no_transfer(seed_test_data):
    """Test updating only DRS boost (should not count as transfer)"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: same drivers, different DRS driver
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": initial_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": initial_drivers[1],  # Changed from [0] to [1]
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert result["drs_boost_driver_id"] == initial_drivers[1]
        assert len(result["transfer_history"]) == 0  # No transfer history
        assert result["current_race_transfers"] == 0


@pytest.mark.asyncio
async def test_update_constructor_swap(seed_test_data):
    """Test swapping constructor"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    initial_constructors = data["budget_constructors"][:2]
    team = await create_test_team(
        initial_drivers, initial_constructors, initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: swap 1 constructor
    new_constructors = [initial_constructors[0], data["budget_constructors"][2]]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": initial_drivers,
                "constructor_ids": new_constructors,
                "drs_boost_driver_id": initial_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["constructors"]) == 2
        assert len(result["transfer_history"]) == 1
        assert result["transfer_history"][0]["transfers_used"] == 1
        assert result["transfer_history"][0]["penalty_points"] == 0


@pytest.mark.asyncio
async def test_update_budget_exceeded_fails(seed_test_data):
    """Test update fails when swapping to expensive driver exceeds budget"""
    data = seed_test_data

    # Create team with budget drivers
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Try to swap to very expensive driver AND expensive constructor (will exceed budget)
    # Budget drivers total ~38M + budget constructors ~11.5M = ~49.5M
    # Swap to expensive driver (30.5M) + expensive constructor (28M) will push it over 100M
    new_drivers = initial_drivers[:4] + data["expensive_drivers"][:1]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": data["expensive_constructors"][:2],  # Use expensive constructors
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 422

        result = response.json()
        assert result["detail"]["code"] == "RULE_VIOLATION"
        assert "violations" in result["detail"]


@pytest.mark.asyncio
async def test_update_nonexistent_team_404(seed_test_data):
    """Test updating non-existent team returns 404"""
    data = seed_test_data

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            "/api/v1/teams/fake-team-id",
            json={
                "driver_ids": data["budget_drivers"][:5],
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": data["budget_drivers"][0],
            },
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_update_no_changes(seed_test_data):
    """Test updating with no actual changes"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update with same data
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": initial_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": initial_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["transfer_history"]) == 0  # No new history record
        assert result["current_race_transfers"] == 0


@pytest.mark.asyncio
async def test_update_driver_and_constructor_swaps(seed_test_data):
    """Test updating with both driver and constructor swaps"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    initial_constructors = data["budget_constructors"][:2]
    team = await create_test_team(
        initial_drivers, initial_constructors, initial_drivers[0]
    )
    team_id = team["team_id"]

    # Update: swap 1 driver and 1 constructor (total 2 transfers)
    new_drivers = initial_drivers[:4] + [data["budget_drivers"][5]]
    new_constructors = [initial_constructors[0], data["budget_constructors"][2]]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": new_constructors,
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert len(result["transfer_history"]) == 1
        assert result["transfer_history"][0]["transfers_used"] == 2
        assert result["transfer_history"][0]["penalty_points"] == 0
        assert len(result["transfer_history"][0]["changes"]) == 4  # 2 out, 2 in


@pytest.mark.asyncio
async def test_update_invalid_drs_boost_fails(seed_test_data):
    """Test update fails when DRS boost assigned to non-selected driver"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Try to assign DRS boost to driver not in team
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": initial_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": data["budget_drivers"][6],  # Not in team
            },
        )

        assert response.status_code == 422


@pytest.mark.asyncio
async def test_update_driver_not_found(seed_test_data):
    """Test update fails when driver doesn't exist"""
    data = seed_test_data

    # Create team
    initial_drivers = data["budget_drivers"][:5]
    team = await create_test_team(
        initial_drivers, data["budget_constructors"][:2], initial_drivers[0]
    )
    team_id = team["team_id"]

    # Try to swap to non-existent driver
    new_drivers = initial_drivers[:4] + ["non-existent-driver"]

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.put(
            f"/api/v1/teams/{team_id}",
            json={
                "driver_ids": new_drivers,
                "constructor_ids": data["budget_constructors"][:2],
                "drs_boost_driver_id": new_drivers[0],
            },
        )

        assert response.status_code == 404
        assert "driver" in response.json()["detail"].lower()
