"""Team Request/Response Schemas"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, field_validator

from app.models.team import DriverSelection, ConstructorSelection


class DriverSelectionInput(BaseModel):
    """Driver selection input"""

    driver_id: str


class ConstructorSelectionInput(BaseModel):
    """Constructor selection input"""

    constructor_id: str


class TeamCreate(BaseModel):
    """Team creation request schema"""

    team_name: str
    driver_ids: List[str]  # Exactly 5
    constructor_ids: List[str]  # Exactly 2
    drs_boost_driver_id: str
    season: int = 2026

    @field_validator("driver_ids")
    @classmethod
    def validate_driver_count(cls, v):
        if len(v) != 5:
            raise ValueError("Must select exactly 5 drivers")
        if len(set(v)) != 5:
            raise ValueError("All drivers must be unique")
        return v

    @field_validator("constructor_ids")
    @classmethod
    def validate_constructor_count(cls, v):
        if len(v) != 2:
            raise ValueError("Must select exactly 2 constructors")
        if len(set(v)) != 2:
            raise ValueError("All constructors must be unique")
        return v

    @field_validator("drs_boost_driver_id")
    @classmethod
    def validate_drs_boost(cls, v, info):
        if "driver_ids" in info.data and v not in info.data["driver_ids"]:
            raise ValueError("DRS Boost must be assigned to one of the selected drivers")
        return v


class TeamResponse(BaseModel):
    """Team response schema"""

    team_id: str
    team_name: str
    created_by: str
    season: int
    drivers: List[DriverSelection]
    constructors: List[ConstructorSelection]
    drs_boost_driver_id: Optional[str]
    budget_cap: float
    budget_used: float
    budget_remaining: float
    is_valid: bool
    validation_errors: List[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
