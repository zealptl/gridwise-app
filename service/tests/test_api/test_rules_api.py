"""Integration Tests for Rules API"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.rule import Rule


@pytest.mark.asyncio
async def test_get_all_rules():
    """Test getting all rules"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have the 7 seeded rules
        assert len(data) >= 7


@pytest.mark.asyncio
async def test_get_all_rules_filter_by_active():
    """Test getting all active rules"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/?is_active=true")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # All returned rules should be active
        for rule in data:
            assert rule["is_active"] is True


@pytest.mark.asyncio
async def test_get_all_rules_filter_by_type():
    """Test getting rules filtered by type"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/?rule_type=budget_cap")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have at least 1 budget cap rule
        assert len(data) >= 1
        assert data[0]["rule_type"] == "budget_cap"


@pytest.mark.asyncio
async def test_get_rule_by_id():
    """Test getting a specific rule by ID"""
    # First get all rules to get an ID
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/")
        rules = response.json()
        rule_id = rules[0]["rule_id"]

        # Now get specific rule
        response = await client.get(f"/api/v1/rules/{rule_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["rule_id"] == rule_id


@pytest.mark.asyncio
async def test_get_rule_not_found():
    """Test getting a non-existent rule"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/nonexistent-id")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_rule():
    """Test creating a new rule"""
    rule_data = {
        "rule_type": "budget_cap",
        "name": "Test Budget Cap",
        "description": "Test rule for budget cap",
        "config": {"max_budget": 100.0},
        "validation_logic": {
            "operator": "<=",
            "field": "budget_used",
            "threshold": "config.max_budget",
            "error_message_template": "Budget exceeded: {budget_used}M / {max_budget}M",
        },
        "severity": "error",
        "is_active": True,
        "applies_to": "team",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/rules/", json=rule_data)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Budget Cap"
        assert "rule_id" in data
        assert data["is_active"] is True

        # Clean up: delete the created rule
        await Rule.find_one(Rule.rule_id == data["rule_id"]).delete()


@pytest.mark.asyncio
async def test_update_rule():
    """Test updating a rule"""
    # First create a rule
    rule_data = {
        "rule_type": "budget_cap",
        "name": "Original Name",
        "description": "Original description",
        "config": {"max_budget": 100.0},
        "validation_logic": {
            "operator": "<=",
            "field": "budget_used",
            "threshold": "config.max_budget",
            "error_message_template": "Test message",
        },
        "severity": "error",
        "is_active": True,
        "applies_to": "team",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/api/v1/rules/", json=rule_data)
        created_rule = create_response.json()
        rule_id = created_rule["rule_id"]

        # Update the rule
        update_data = {
            "name": "Updated Name",
            "description": "Updated description",
        }

        response = await client.put(f"/api/v1/rules/{rule_id}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

        # Clean up
        await Rule.find_one(Rule.rule_id == rule_id).delete()


@pytest.mark.asyncio
async def test_delete_rule():
    """Test soft-deleting a rule"""
    # First create a rule
    rule_data = {
        "rule_type": "budget_cap",
        "name": "To Delete",
        "description": "Will be deleted",
        "config": {"max_budget": 100.0},
        "validation_logic": {
            "operator": "<=",
            "field": "budget_used",
            "threshold": "config.max_budget",
            "error_message_template": "Test",
        },
        "severity": "error",
        "is_active": True,
        "applies_to": "team",
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        create_response = await client.post("/api/v1/rules/", json=rule_data)
        created_rule = create_response.json()
        rule_id = created_rule["rule_id"]

        # Delete the rule
        response = await client.delete(f"/api/v1/rules/{rule_id}")

        assert response.status_code == 204

        # Verify it's soft-deleted (is_active = False)
        get_response = await client.get(f"/api/v1/rules/{rule_id}")
        data = get_response.json()
        assert data["is_active"] is False

        # Clean up
        await Rule.find_one(Rule.rule_id == rule_id).delete()


@pytest.mark.asyncio
async def test_toggle_rule():
    """Test toggling rule active status"""
    # Get an existing rule
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/rules/")
        rules = response.json()
        rule_id = rules[0]["rule_id"]
        original_status = rules[0]["is_active"]

        # Toggle the rule
        response = await client.patch(f"/api/v1/rules/{rule_id}/toggle")

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] != original_status

        # Toggle back
        response = await client.patch(f"/api/v1/rules/{rule_id}/toggle")
        data = response.json()
        assert data["is_active"] == original_status
