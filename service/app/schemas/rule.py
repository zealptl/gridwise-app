"""Rule API Schemas"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.models.rule import RuleSeverity, RuleType, ValidationLogic


class RuleBase(BaseModel):
    """Base rule schema"""

    rule_type: RuleType
    name: str
    description: str
    config: Dict[str, Any]
    validation_logic: ValidationLogic
    severity: RuleSeverity = RuleSeverity.ERROR
    applies_to: str


class RuleCreate(RuleBase):
    """Schema for creating a rule"""

    is_active: bool = True


class RuleUpdate(BaseModel):
    """Schema for updating a rule"""

    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    validation_logic: Optional[ValidationLogic] = None
    severity: Optional[RuleSeverity] = None
    is_active: Optional[bool] = None


class RuleResponse(RuleBase):
    """Schema for rule response"""

    rule_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

    class Config:
        from_attributes = True
