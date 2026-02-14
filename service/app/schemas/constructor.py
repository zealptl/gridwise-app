from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class PriceHistory(BaseModel):
    price: float
    changed_at: datetime
    changed_by: str = "system"

class ConstructorBase(BaseModel):
    name: str
    full_name: str
    nationality: str
    price: float
    status: str = "active"

class ConstructorCreate(ConstructorBase):
    pass

class ConstructorUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    nationality: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None

class ConstructorResponse(ConstructorBase):
    constructor_id: str
    price_history: List[PriceHistory] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
