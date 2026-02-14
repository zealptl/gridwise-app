"""Pytest Configuration and Fixtures"""
import pytest
import pytest_asyncio
from httpx import AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings
from app.main import app
from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.rule import Rule
from app.models.team import FantasyTeam
from app.models.user import User


@pytest_asyncio.fixture(scope="function", autouse=True)
async def initialize_database():
    """Initialize database connection for tests"""
    from beanie import init_beanie

    # Create MongoDB client
    client = AsyncIOMotorClient(settings.MONGODB_URL)

    # Initialize Beanie with document models
    await init_beanie(
        database=client[settings.MONGODB_DB_NAME],
        document_models=[
            Driver,
            Constructor,
            Rule,
            FantasyTeam,
            User,
        ],
    )

    yield

    # Cleanup: close connection after test
    client.close()


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
