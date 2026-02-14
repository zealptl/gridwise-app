"""Rule Model"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from beanie import Document
from pydantic import BaseModel, Field


class RuleType(str, Enum):
    """Rule type enumeration"""

    BUDGET_CAP = "budget_cap"
    ROSTER_SIZE = "roster_size"
    DRS_BOOST_REQUIRED = "drs_boost_required"
    MAX_TEAMS_PER_USER = "max_teams_per_user"
    TRANSFER_LIMIT = "transfer_limit"
    DRIVER_ELIGIBILITY = "driver_eligibility"


class RuleSeverity(str, Enum):
    """Rule severity enumeration"""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationLogic(BaseModel):
    """Validation logic configuration"""

    operator: str  # "<=", "==", "in", "custom"
    field: str  # "budget_used", "len(drivers)", etc.
    threshold: str  # Reference to config value or literal
    error_message_template: str
    function: Optional[str] = None  # For custom validators


class Rule(Document):
    """Rule document model"""

    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_type: RuleType
    name: str
    description: str
    config: Dict[str, Any]  # Flexible configuration
    validation_logic: ValidationLogic
    severity: RuleSeverity = RuleSeverity.ERROR
    is_active: bool = True
    applies_to: str  # "team", "user", "driver"

    # Versioning (for future)
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"

    class Settings:
        name = "rules"
        indexes = [
            "rule_id",
            "rule_type",
            "is_active",
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "rule_type": "budget_cap",
                "name": "Budget Cap Rule",
                "description": "Total team cost must not exceed the cost cap",
                "config": {"max_budget": 100.0, "currency": "M"},
                "validation_logic": {
                    "operator": "<=",
                    "field": "budget_used",
                    "threshold": "config.max_budget",
                    "error_message_template": "Budget exceeded: {budget_used}M / {max_budget}M",
                },
                "severity": "error",
                "is_active": True,
                "applies_to": "team",
            }
        }
