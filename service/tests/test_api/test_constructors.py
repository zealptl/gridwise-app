"""Integration tests for Constructor API endpoints"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_create_constructor():
    """Test creating a new constructor"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        constructor_data = {
            "name": "Red Bull",
            "full_name": "Oracle Red Bull Racing",
            "nationality": "Austrian",
            "price": 28.0,
            "status": "active"
        }

        response = await client.post("/api/v1/constructors/", json=constructor_data)
        assert response.status_code == 201

        data = response.json()
        assert data["name"] == "Red Bull"
        assert data["full_name"] == "Oracle Red Bull Racing"
        assert data["nationality"] == "Austrian"
        assert "constructor_id" in data
        assert "price_history" in data
        assert len(data["price_history"]) == 1
        assert data["price_history"][0]["price"] == 28.0


@pytest.mark.asyncio
async def test_get_all_constructors():
    """Test getting all constructors"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/constructors/")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_constructor_by_id():
    """Test getting a specific constructor by ID"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # First create a constructor
        constructor_data = {
            "name": "Ferrari",
            "full_name": "Scuderia Ferrari",
            "nationality": "Italian",
            "price": 26.5,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]

        # Get the constructor by ID
        response = await client.get(f"/api/v1/constructors/{constructor_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["constructor_id"] == constructor_id
        assert data["name"] == "Ferrari"
        assert data["full_name"] == "Scuderia Ferrari"


@pytest.mark.asyncio
async def test_get_constructor_not_found():
    """Test getting a non-existent constructor returns 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/constructors/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_filter_constructors_by_status():
    """Test filtering constructors by status"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create an active constructor
        active_constructor = {
            "name": "McLaren",
            "full_name": "McLaren Formula 1 Team",
            "nationality": "British",
            "price": 23.5,
            "status": "active"
        }
        await client.post("/api/v1/constructors/", json=active_constructor)

        # Filter by active status
        response = await client.get("/api/v1/constructors/?status=active")
        assert response.status_code == 200

        data = response.json()
        assert all(c["status"] == "active" for c in data)


@pytest.mark.asyncio
async def test_update_constructor():
    """Test updating constructor information"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a constructor
        constructor_data = {
            "name": "Mercedes",
            "full_name": "Mercedes-AMG Petronas F1 Team",
            "nationality": "German",
            "price": 25.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]

        # Update the constructor
        update_data = {
            "full_name": "Mercedes-AMG Petronas Formula One Team",
            "price": 27.0
        }

        response = await client.put(f"/api/v1/constructors/{constructor_id}", json=update_data)
        assert response.status_code == 200

        updated_constructor = response.json()
        assert updated_constructor["full_name"] == "Mercedes-AMG Petronas Formula One Team"
        assert updated_constructor["price"] == 27.0
        assert updated_constructor["name"] == "Mercedes"  # Unchanged


@pytest.mark.asyncio
async def test_update_constructor_price_tracks_history():
    """Test that price changes are tracked in history"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a constructor
        constructor_data = {
            "name": "Aston Martin",
            "full_name": "Aston Martin Aramco F1 Team",
            "nationality": "British",
            "price": 21.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]
        original_price = created_constructor["price"]

        # Update price
        new_price = 24.5
        response = await client.put(
            f"/api/v1/constructors/{constructor_id}",
            json={"price": new_price}
        )
        assert response.status_code == 200

        updated_constructor = response.json()
        assert updated_constructor["price"] == new_price
        assert len(updated_constructor["price_history"]) == 2
        assert updated_constructor["price_history"][0]["price"] == original_price
        assert updated_constructor["price_history"][1]["price"] == new_price


@pytest.mark.asyncio
async def test_update_constructor_not_found():
    """Test updating a non-existent constructor returns 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        update_data = {"price": 30.0}
        response = await client.put("/api/v1/constructors/nonexistent-id", json=update_data)
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_constructor_soft_delete():
    """Test that delete performs soft delete (sets status=inactive)"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a constructor
        constructor_data = {
            "name": "Alpine",
            "full_name": "BWT Alpine F1 Team",
            "nationality": "French",
            "price": 18.5,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]

        # Delete the constructor
        delete_response = await client.delete(f"/api/v1/constructors/{constructor_id}")
        assert delete_response.status_code == 204

        # Verify constructor still exists but is inactive
        get_response = await client.get(f"/api/v1/constructors/{constructor_id}")
        assert get_response.status_code == 200

        constructor = get_response.json()
        assert constructor["status"] == "inactive"


@pytest.mark.asyncio
async def test_delete_constructor_not_found():
    """Test deleting a non-existent constructor returns 404"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete("/api/v1/constructors/nonexistent-id")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_pagination():
    """Test pagination with skip and limit"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create multiple constructors
        for i in range(5):
            constructor_data = {
                "name": f"Team{i}",
                "full_name": f"Full Team Name {i}",
                "nationality": "Test",
                "price": 15.0 + i,
                "status": "active"
            }
            await client.post("/api/v1/constructors/", json=constructor_data)

        # Test pagination
        response = await client.get("/api/v1/constructors/?skip=0&limit=2")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 2


@pytest.mark.asyncio
async def test_update_constructor_partial():
    """Test partial update of constructor fields"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a constructor
        constructor_data = {
            "name": "Williams",
            "full_name": "Williams Racing",
            "nationality": "British",
            "price": 16.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]

        # Update only the price
        update_data = {"price": 17.5}

        response = await client.put(f"/api/v1/constructors/{constructor_id}", json=update_data)
        assert response.status_code == 200

        updated_constructor = response.json()
        assert updated_constructor["price"] == 17.5
        assert updated_constructor["name"] == "Williams"
        assert updated_constructor["full_name"] == "Williams Racing"
        assert updated_constructor["nationality"] == "British"
        assert updated_constructor["status"] == "active"


@pytest.mark.asyncio
async def test_price_history_unchanged_when_price_not_updated():
    """Test that price history is not modified when price is not changed"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create a constructor
        constructor_data = {
            "name": "Haas",
            "full_name": "MoneyGram Haas F1 Team",
            "nationality": "American",
            "price": 15.0,
            "status": "active"
        }

        create_response = await client.post("/api/v1/constructors/", json=constructor_data)
        created_constructor = create_response.json()
        constructor_id = created_constructor["constructor_id"]

        # Update name but not price
        update_data = {"full_name": "Haas F1 Team"}

        response = await client.put(f"/api/v1/constructors/{constructor_id}", json=update_data)
        assert response.status_code == 200

        updated_constructor = response.json()
        # Price history should still have only 1 entry (initial)
        assert len(updated_constructor["price_history"]) == 1
        assert updated_constructor["price_history"][0]["price"] == 15.0
