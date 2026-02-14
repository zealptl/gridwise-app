"""Validation Models"""

from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class ValidationStatus(str, Enum):
    """Validation status enumeration"""

    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"


class RuleViolation(BaseModel):
    """Rule violation details"""

    rule_id: str
    rule_name: str
    rule_type: str
    severity: str  # "error", "warning", "info"
    message: str
    details: Dict[str, Any]


class TeamValidationResult(BaseModel):
    """Team validation result"""

    team_id: str
    status: ValidationStatus
    is_valid: bool
    violations: List[RuleViolation] = []
    warnings: List[RuleViolation] = []
    info: List[RuleViolation] = []
    summary: Dict[str, Any]
