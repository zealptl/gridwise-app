"""Database Connection and Initialization"""

from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.config import settings


class Database:
    """Database connection manager"""

    client: Optional[AsyncIOMotorClient] = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB and initialize Beanie ODM"""
    try:
        # Import models here to avoid circular imports
        from app.models.constructor import Constructor
        from app.models.driver import Driver
        from app.models.rule import Rule
        from app.models.team import FantasyTeam
        from app.models.user import User

        # Create MongoDB client
        db.client = AsyncIOMotorClient(settings.MONGODB_URL)

        # Initialize Beanie with document models
        await init_beanie(
            database=db.client[settings.MONGODB_DB_NAME],
            document_models=[
                Driver,
                Constructor,
                Rule,
                FantasyTeam,
                User,
            ],
        )

        print(f"Connected to MongoDB at {settings.MONGODB_URL}")
        print(f"Database: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")
        print("Note: This is expected if MongoDB is not yet installed")


async def close_mongo_connection():
    """Close MongoDB connection"""
    if db.client:
        db.client.close()
        print("Closed MongoDB connection")


async def get_database():
    """Get database instance"""
    if db.client is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db.client[settings.MONGODB_DB_NAME]
