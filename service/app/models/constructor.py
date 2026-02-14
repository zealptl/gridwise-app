"""Constructor Model"""

from datetime import datetime
from typing import List
from uuid import uuid4

from beanie import Document
from pydantic import Field


class Constructor(Document):
    """F1 Constructor (Team) document model"""

    constructor_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    full_name: str
    nationality: str
    price: float  # In millions (M)
    status: str = "active"  # active, inactive

    # Price history
    price_history: List[dict] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "constructors"
        indexes = [
            "constructor_id",
            "status",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "constructor_id": "con-123",
                "name": "Red Bull",
                "full_name": "Oracle Red Bull Racing",
                "nationality": "Austrian",
                "price": 28.0,
                "status": "active",
            }
        }
