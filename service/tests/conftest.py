"""Pytest Configuration and Fixtures"""
import pytest
from httpx import AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Async test client for FastAPI application"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_driver_data():
    """Sample driver data for testing"""
    return {
        "name": "Max Verstappen",
        "number": 1,
        "team": "Red Bull Racing",
        "country": "Netherlands",
    }


@pytest.fixture
def sample_constructor_data():
    """Sample constructor data for testing"""
    return {
        "name": "Red Bull Racing",
        "country": "Austria",
        "base": "Milton Keynes, UK",
    }


@pytest.fixture
def sample_rule_data():
    """Sample rule data for testing"""
    return {
        "name": "Points per Position",
        "type": "position_points",
        "enabled": True,
        "config": {"positions": {1: 25, 2: 18, 3: 15}},
    }
