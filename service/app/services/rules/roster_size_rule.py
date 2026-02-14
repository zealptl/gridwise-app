"""Roster Size Rule Validator"""

from typing import Optional

from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class RosterSizeRule(AbstractRule):
    """
    Validates that team has the correct number of drivers and/or constructors.

    Configuration:
        - required_drivers: Required number of drivers (if validating drivers)
        - required_constructors: Required number of constructors (if validating constructors)
        - min_drivers: Minimum drivers allowed
        - max_drivers: Maximum drivers allowed
        - min_constructors: Minimum constructors allowed
        - max_constructors: Maximum constructors allowed
    """

    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Check if team has correct roster size.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if roster size invalid, None otherwise
        """
        # Check if this rule is for drivers
        if "required_drivers" in self.config:
            required = self.config["required_drivers"]
            actual = len(team.drivers)

            if actual != required:
                message = self.validation_logic.error_message_template.format(
                    actual=actual,
                    required=required,
                )

                return self.create_violation(
                    message=message,
                    details={
                        "required_drivers": required,
                        "actual_drivers": actual,
                        "difference": actual - required,
                    },
                )

        # Check if this rule is for constructors
        if "required_constructors" in self.config:
            required = self.config["required_constructors"]
            actual = len(team.constructors)

            if actual != required:
                message = self.validation_logic.error_message_template.format(
                    actual=actual,
                    required=required,
                )

                return self.create_violation(
                    message=message,
                    details={
                        "required_constructors": required,
                        "actual_constructors": actual,
                        "difference": actual - required,
                    },
                )

        return None
