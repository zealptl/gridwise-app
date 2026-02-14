from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PriceHistory(BaseModel):
    price: float
    changed_at: datetime
    changed_by: str = "system"

class DriverBase(BaseModel):
    first_name: str
    last_name: str
    team_name: str
    nationality: str
    driver_number: int
    price: float
    status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team_name: Optional[str] = None
    nationality: Optional[str] = None
    driver_number: Optional[int] = None
    price: Optional[float] = None
    status: Optional[str] = None

class DriverResponse(DriverBase):
    driver_id: str
    price_history: List[PriceHistory] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
