"""Fantasy Team Model"""

from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, Field


class DriverSelection(BaseModel):
    """Driver selection in a fantasy team"""

    driver_id: str
    driver_name: str
    team_name: str
    price: float


class ConstructorSelection(BaseModel):
    """Constructor selection in a fantasy team"""

    constructor_id: str
    constructor_name: str
    price: float


class TransferRecord(BaseModel):
    """Record of transfers made for a race"""

    race_id: Optional[str] = None
    transfers_used: int
    transfers_available: int
    penalty_points: int
    changes: List[dict]
    timestamp: datetime


class FantasyTeam(Document):
    """Fantasy Team document model"""

    team_id: str = Field(default_factory=lambda: str(uuid4()))
    team_name: str
    created_by: str  # user_id

    # Season context
    season: int = 2026
    current_race_id: Optional[str] = None

    # Team composition
    drivers: List[DriverSelection] = Field(default_factory=list)
    constructors: List[ConstructorSelection] = Field(default_factory=list)

    # DRS Boost
    drs_boost_driver_id: Optional[str] = None

    # Budget tracking
    budget_cap: float = 100.0
    budget_used: float = 0.0
    budget_remaining: float = 100.0

    # Transfer tracking
    transfer_history: List[TransferRecord] = Field(default_factory=list)
    current_race_transfers: int = 0
    available_transfers: int = 2

    # Validation status
    is_valid: bool = False
    last_validated_at: Optional[datetime] = None
    validation_errors: List[dict] = Field(default_factory=list)

    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "teams"
        indexes = [
            "team_id",
            "created_by",
            "season",
            "is_valid",
            "is_active",
        ]

    def calculate_budget(self):
        """Calculate budget used and remaining"""
        total_drivers = sum(d.price for d in self.drivers)
        total_constructors = sum(c.price for c in self.constructors)
        self.budget_used = total_drivers + total_constructors
        self.budget_remaining = self.budget_cap - self.budget_used
