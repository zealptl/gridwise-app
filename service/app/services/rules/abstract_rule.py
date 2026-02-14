"""Abstract Rule Base Class"""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.rule import Rule
from app.models.team import FantasyTeam
from app.models.validation import RuleViolation


class AbstractRule(ABC):
    """
    Abstract base class for all rule validators.
    Each rule type extends this class and implements its own runRule() method.
    """

    def __init__(self, rule: Rule):
        """Initialize rule with configuration from database."""
        self.rule_id = rule.rule_id
        self.rule_type = rule.rule_type
        self.name = rule.name
        self.description = rule.description
        self.config = rule.config
        self.validation_logic = rule.validation_logic
        self.severity = rule.severity
        self.is_active = rule.is_active
        self.applies_to = rule.applies_to

    @abstractmethod
    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Execute rule validation against a team.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if validation fails, None if passes
        """
        pass

    def create_violation(self, message: str, details: dict) -> RuleViolation:
        """Helper method to create a RuleViolation object."""
        return RuleViolation(
            rule_id=self.rule_id,
            rule_name=self.name,
            rule_type=self.rule_type.value,
            severity=self.severity.value,
            message=message,
            details=details,
        )
