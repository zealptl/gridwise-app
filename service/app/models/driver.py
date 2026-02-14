"""Driver Model"""

from datetime import datetime
from typing import List
from uuid import uuid4

from beanie import Document
from pydantic import Field


class Driver(Document):
    """F1 Driver document model"""

    driver_id: str = Field(default_factory=lambda: str(uuid4()))
    first_name: str
    last_name: str
    team_name: str  # Constructor they drive for
    nationality: str
    driver_number: int
    price: float  # In millions (M)
    status: str = "active"  # active, inactive, reserve

    # Price history for tracking
    price_history: List[dict] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "drivers"
        indexes = [
            "driver_id",
            "team_name",
            "status",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "driver_id": "drv-123",
                "first_name": "Max",
                "last_name": "Verstappen",
                "team_name": "Red Bull Racing",
                "nationality": "Dutch",
                "driver_number": 1,
                "price": 30.5,
                "status": "active",
            }
        }
