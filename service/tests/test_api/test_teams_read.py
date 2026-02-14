"""Integration Tests for View Teams API"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam


@pytest.fixture
async def sample_teams():
    """Create sample teams for testing"""
    teams = []

    # Team 1 - Valid team for 2026
    team1 = FantasyTeam(
        team_name="Team Alpha",
        created_by="user1",
        season=2026,
        drivers=[
            DriverSelection(
                driver_id=f"d{i}",
                driver_name=f"Driver {i}",
                team_name="Team A",
                price=15.0,
            )
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(
                constructor_id=f"c{i}",
                constructor_name=f"Constructor {i}",
                price=12.5,
            )
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
        is_valid=True,
    )
    team1.calculate_budget()
    await team1.insert()
    teams.append(team1)

    # Team 2 - Invalid team for 2026
    team2 = FantasyTeam(
        team_name="Team Beta",
        created_by="user1",
        season=2026,
        drivers=[
            DriverSelection(
                driver_id=f"d{i}",
                driver_name=f"Driver {i}",
                team_name="Team B",
                price=25.0,
            )
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(
                constructor_id=f"c{i}",
                constructor_name=f"Constructor {i}",
                price=20.0,
            )
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
        is_valid=False,
    )
    team2.calculate_budget()
    await team2.insert()
    teams.append(team2)

    # Team 3 - Valid team for 2025
    team3 = FantasyTeam(
        team_name="Team Gamma",
        created_by="user2",
        season=2025,
        drivers=[
            DriverSelection(
                driver_id=f"d{i}",
                driver_name=f"Driver {i}",
                team_name="Team C",
                price=10.0,
            )
            for i in range(5)
        ],
        constructors=[
            ConstructorSelection(
                constructor_id=f"c{i}",
                constructor_name=f"Constructor {i}",
                price=10.0,
            )
            for i in range(2)
        ],
        drs_boost_driver_id="d0",
        is_valid=True,
    )
    team3.calculate_budget()
    await team3.insert()
    teams.append(team3)

    yield teams

    # Cleanup
    for team in teams:
        await team.delete()


@pytest.mark.asyncio
async def test_get_all_teams(sample_teams):
    """Test getting all teams without filters"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/teams/")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "skip" in data
        assert "limit" in data
        assert "teams" in data

        assert data["total"] >= 3
        assert data["skip"] == 0
        assert data["limit"] == 20
        assert len(data["teams"]) >= 3

        # Verify team summary structure
        team = data["teams"][0]
        assert "team_id" in team
        assert "team_name" in team
        assert "season" in team
        assert "budget_used" in team
        assert "budget_remaining" in team
        assert "is_valid" in team
        assert "driver_count" in team
        assert "constructor_count" in team
        assert "created_at" in team
        assert "updated_at" in team


@pytest.mark.asyncio
async def test_filter_by_season(sample_teams):
    """Test filtering teams by season"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/teams/?season=2026")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2
        # All returned teams should be for season 2026
        for team in data["teams"]:
            assert team["season"] == 2026


@pytest.mark.asyncio
async def test_filter_by_is_valid(sample_teams):
    """Test filtering teams by validation status"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Get valid teams
        response = await client.get("/api/v1/teams/?is_valid=true")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2
        for team in data["teams"]:
            assert team["is_valid"] is True

        # Get invalid teams
        response = await client.get("/api/v1/teams/?is_valid=false")
        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 1
        for team in data["teams"]:
            assert team["is_valid"] is False


@pytest.mark.asyncio
async def test_filter_by_created_by(sample_teams):
    """Test filtering teams by user"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/teams/?created_by=user1")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] >= 2
        # Note: We can't verify created_by in response since it's not in TeamSummary
        # But we know from our fixture that user1 has 2 teams


@pytest.mark.asyncio
async def test_pagination(sample_teams):
    """Test pagination works correctly"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Get first page with limit=2
        response = await client.get("/api/v1/teams/?skip=0&limit=2")
        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 0
        assert data["limit"] == 2
        assert len(data["teams"]) <= 2

        # Get second page
        response = await client.get("/api/v1/teams/?skip=2&limit=2")
        assert response.status_code == 200
        data = response.json()

        assert data["skip"] == 2
        assert data["limit"] == 2


@pytest.mark.asyncio
async def test_combined_filters(sample_teams):
    """Test combining multiple filters"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/v1/teams/?season=2026&is_valid=true&created_by=user1"
        )

        assert response.status_code == 200
        data = response.json()

        # Should return Team Alpha only
        assert data["total"] >= 1
        for team in data["teams"]:
            assert team["season"] == 2026
            assert team["is_valid"] is True


@pytest.mark.asyncio
async def test_get_team_by_id(sample_teams):
    """Test getting a specific team by ID"""
    team = sample_teams[0]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/teams/{team.team_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["team_id"] == team.team_id
        assert data["team_name"] == team.team_name
        assert data["season"] == team.season
        assert "drivers" in data
        assert "constructors" in data
        assert len(data["drivers"]) == 5
        assert len(data["constructors"]) == 2
        assert "drs_boost_driver_id" in data
        assert "budget_cap" in data
        assert "budget_used" in data
        assert "budget_remaining" in data
        assert "is_valid" in data
        assert "validation_errors" in data


@pytest.mark.asyncio
async def test_get_team_full_details(sample_teams):
    """Test that full team details are returned"""
    team = sample_teams[0]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(f"/api/v1/teams/{team.team_id}")

        assert response.status_code == 200
        data = response.json()

        # Verify driver details
        assert isinstance(data["drivers"], list)
        driver = data["drivers"][0]
        assert "driver_id" in driver
        assert "driver_name" in driver
        assert "team_name" in driver
        assert "price" in driver

        # Verify constructor details
        assert isinstance(data["constructors"], list)
        constructor = data["constructors"][0]
        assert "constructor_id" in constructor
        assert "constructor_name" in constructor
        assert "price" in constructor


@pytest.mark.asyncio
async def test_get_nonexistent_team():
    """Test getting a team that doesn't exist"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/teams/nonexistent-team-id")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


@pytest.mark.asyncio
async def test_teams_sorted_by_created_at(sample_teams):
    """Test that teams are sorted by created_at DESC (most recent first)"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/v1/teams/")

        assert response.status_code == 200
        data = response.json()

        if len(data["teams"]) > 1:
            # Verify teams are in descending order by created_at
            for i in range(len(data["teams"]) - 1):
                current_time = data["teams"][i]["created_at"]
                next_time = data["teams"][i + 1]["created_at"]
                assert current_time >= next_time


@pytest.mark.asyncio
async def test_empty_result_set():
    """Test that empty result set returns empty array"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Query for a season that doesn't exist
        response = await client.get("/api/v1/teams/?season=1999")

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 0
        assert data["teams"] == []


@pytest.mark.asyncio
async def test_limit_validation():
    """Test that limit parameter is validated"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Try to exceed max limit
        response = await client.get("/api/v1/teams/?limit=200")

        # Should return validation error (422)
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_skip_validation():
    """Test that skip parameter is validated"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # Try negative skip
        response = await client.get("/api/v1/teams/?skip=-1")

        # Should return validation error (422)
        assert response.status_code == 422
