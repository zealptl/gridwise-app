"""Integration tests for Driver API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_driver():
    """Test creating a new driver"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        driver_data = {
            "first_name": "Lewis",
            "last_name": "Hamilton",
            "team_name": "Mercedes",
            "nationality": "British",
            "driver_number": 44,
            "price": 28.0,
            "status": "active"
        }

        response = await client.post("/api/v1/drivers/", json=driver_data)
        assert response.status_code == 201

        data = response.json()
        assert data["first_name"] == "Lewis"
        assert data["last_name"] == "Hamilton"
        assert data["driver_number"] == 44
        assert "driver_id" in data
        assert "price_history" in data
        assert len(data["price_history"]) == 1
        assert data["price_history"][0]["price"] == 28.0


@pytest.mark.asyncio
async def test_get_all_drivers():
    """Test getting all drivers"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/drivers/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_driver_by_id():
    """Test getting a specific driver by ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First create a driver
        driver_data = {
            "first_name": "George",
            "last_name": "Russell",
            "team_name": "Mercedes",
            "nationality": "British",
            "driver_number": 63,
            "price": 24.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/drivers/", json=driver_data)
        created_driver = create_response.json()
        driver_id = created_driver["driver_id"]

        # Get the driver by ID
        response = await client.get(f"/api/v1/drivers/{driver_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["driver_id"] == driver_id
        assert data["first_name"] == "George"
        assert data["last_name"] == "Russell"


@pytest.mark.asyncio
async def test_get_driver_not_found():
    """Test getting a non-existent driver returns 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/drivers/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_filter_drivers_by_team():
    """Test filtering drivers by team"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create multiple drivers
        drivers = [
            {
                "first_name": "Max",
                "last_name": "Verstappen",
                "team_name": "Red Bull Racing",
                "nationality": "Dutch",
                "driver_number": 1,
                "price": 30.5,
                "status": "active"
            },
            {
                "first_name": "Sergio",
                "last_name": "Perez",
                "team_name": "Red Bull Racing",
                "nationality": "Mexican",
                "driver_number": 11,
                "price": 26.0,
                "status": "active"
            }
        ]

        for driver in drivers:
            await client.post("/api/v1/drivers/", json=driver)

        # Filter by team
        response = await client.get("/api/v1/drivers/?team_name=Red Bull Racing")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 2
        assert all(d["team_name"] == "Red Bull Racing" for d in data)


@pytest.mark.asyncio
async def test_filter_drivers_by_status():
    """Test filtering drivers by status"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create an active driver
        active_driver = {
            "first_name": "Lando",
            "last_name": "Norris",
            "team_name": "McLaren",
            "nationality": "British",
            "driver_number": 4,
            "price": 25.0,
            "status": "active"
        }
        await client.post("/api/v1/drivers/", json=active_driver)

        # Filter by active status
        response = await client.get("/api/v1/drivers/?status=active")
        assert response.status_code == 200

        data = response.json()
        assert all(d["status"] == "active" for d in data)


@pytest.mark.asyncio
async def test_update_driver():
    """Test updating driver information"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a driver
        driver_data = {
            "first_name": "Charles",
            "last_name": "Leclerc",
            "team_name": "Ferrari",
            "nationality": "Monegasque",
            "driver_number": 16,
            "price": 29.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/drivers/", json=driver_data)
        created_driver = create_response.json()
        driver_id = created_driver["driver_id"]

        # Update the driver
        update_data = {
            "team_name": "Scuderia Ferrari",
            "driver_number": 55
        }

        response = await client.put(f"/api/v1/drivers/{driver_id}", json=update_data)
        assert response.status_code == 200

        updated_driver = response.json()
        assert updated_driver["team_name"] == "Scuderia Ferrari"
        assert updated_driver["driver_number"] == 55
        assert updated_driver["first_name"] == "Charles"  # Unchanged


@pytest.mark.asyncio
async def test_update_driver_price_tracks_history():
    """Test that price changes are tracked in history"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a driver
        driver_data = {
            "first_name": "Fernando",
            "last_name": "Alonso",
            "team_name": "Aston Martin",
            "nationality": "Spanish",
            "driver_number": 14,
            "price": 27.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/drivers/", json=driver_data)
        created_driver = create_response.json()
        driver_id = created_driver["driver_id"]
        original_price = created_driver["price"]

        # Update price
        new_price = 32.0
        response = await client.put(
            f"/api/v1/drivers/{driver_id}",
            json={"price": new_price}
        )
        assert response.status_code == 200

        updated_driver = response.json()
        assert updated_driver["price"] == new_price
        assert len(updated_driver["price_history"]) == 2
        assert updated_driver["price_history"][0]["price"] == original_price
        assert updated_driver["price_history"][1]["price"] == new_price


@pytest.mark.asyncio
async def test_delete_driver_soft_delete():
    """Test that delete performs soft delete (sets status=inactive)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a driver
        driver_data = {
            "first_name": "Lance",
            "last_name": "Stroll",
            "team_name": "Aston Martin",
            "nationality": "Canadian",
            "driver_number": 18,
            "price": 22.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/drivers/", json=driver_data)
        created_driver = create_response.json()
        driver_id = created_driver["driver_id"]

        # Delete the driver
        delete_response = await client.delete(f"/api/v1/drivers/{driver_id}")
        assert delete_response.status_code == 204

        # Verify driver still exists but is inactive
        get_response = await client.get(f"/api/v1/drivers/{driver_id}")
        assert get_response.status_code == 200

        driver = get_response.json()
        assert driver["status"] == "inactive"


@pytest.mark.asyncio
async def test_delete_driver_not_found():
    """Test deleting a non-existent driver returns 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/api/v1/drivers/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination():
    """Test pagination with skip and limit"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create multiple drivers
        for i in range(5):
            driver_data = {
                "first_name": f"Driver{i}",
                "last_name": f"Test{i}",
                "team_name": "Test Team",
                "nationality": "Test",
                "driver_number": 90 + i,
                "price": 20.0 + i,
                "status": "active"
            }
            await client.post("/api/v1/drivers/", json=driver_data)

        # Test pagination
        response = await client.get("/api/v1/drivers/?skip=0&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 2


@pytest.mark.asyncio
async def test_get_drivers_by_team_endpoint():
    """Test the /team/{team_name} endpoint"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create drivers for Ferrari
        drivers = [
            {
                "first_name": "Charles",
                "last_name": "Leclerc",
                "team_name": "Ferrari",
                "nationality": "Monegasque",
                "driver_number": 16,
                "price": 29.0,
                "status": "active"
            },
            {
                "first_name": "Carlos",
                "last_name": "Sainz",
                "team_name": "Ferrari",
                "nationality": "Spanish",
                "driver_number": 55,
                "price": 27.5,
                "status": "active"
            }
        ]

        for driver in drivers:
            await client.post("/api/v1/drivers/", json=driver)

        # Get Ferrari drivers
        response = await client.get("/api/v1/drivers/team/Ferrari")
        assert response.status_code == 200

        data = response.json()
        assert len(data) >= 2
        assert all(d["team_name"] == "Ferrari" for d in data)


@pytest.mark.asyncio
async def test_get_drivers_by_team_not_found():
    """Test getting drivers for a non-existent team"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/drivers/team/NonExistentTeam123")
        assert response.status_code == 404
        assert "no drivers found" in response.json()["detail"].lower()
