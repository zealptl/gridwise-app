"""DRS Boost Assignment Rule Validator"""

from typing import Optional

from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class DRSBoostRule(AbstractRule):
    """
    Validates that DRS Boost is assigned to one of the selected drivers.

    Configuration:
        - required: Whether DRS Boost assignment is required (default: True)
    """

    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Check if DRS Boost is properly assigned.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if DRS Boost not properly assigned, None otherwise
        """
        required = self.config.get("required", True)

        if not required:
            return None

        # Check if DRS Boost is assigned
        if not team.drs_boost_driver_id:
            return self.create_violation(
                message="DRS Boost must be assigned to a driver",
                details={
                    "drs_boost_driver_id": None,
                    "available_drivers": [d.driver_id for d in team.drivers],
                },
            )

        # Check if DRS Boost is assigned to one of the selected drivers
        driver_ids = [d.driver_id for d in team.drivers]

        if team.drs_boost_driver_id not in driver_ids:
            # Get driver name if available
            driver_names = {d.driver_id: f"{d.driver_name}" for d in team.drivers}

            message = self.validation_logic.error_message_template

            return self.create_violation(
                message=message,
                details={
                    "drs_boost_driver_id": team.drs_boost_driver_id,
                    "selected_driver_ids": driver_ids,
                    "selected_driver_names": list(driver_names.values()),
                },
            )

        return None
