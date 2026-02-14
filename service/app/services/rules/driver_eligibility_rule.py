"""Driver Eligibility Rule Validator"""

from typing import List, Optional

from app.models.driver import Driver
from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class DriverEligibilityRule(AbstractRule):
    """
    Validates that all selected drivers are eligible (active status).

    Configuration:
        - allowed_statuses: List of allowed driver statuses (default: ["active"])
    """

    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Check if all drivers are eligible.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if ineligible drivers found, None otherwise
        """
        allowed_statuses = self.config.get("allowed_statuses", ["active"])

        # Get all driver IDs from team
        driver_ids = [d.driver_id for d in team.drivers]

        if not driver_ids:
            return None

        # Query drivers from database
        drivers = await Driver.find({"driver_id": {"$in": driver_ids}}).to_list()

        # Check for ineligible drivers
        ineligible_drivers: List[dict] = []

        for driver in drivers:
            if driver.status not in allowed_statuses:
                ineligible_drivers.append(
                    {
                        "driver_id": driver.driver_id,
                        "driver_name": f"{driver.first_name} {driver.last_name}",
                        "status": driver.status,
                        "team_name": driver.team_name,
                    }
                )

        if ineligible_drivers:
            # Create message for first ineligible driver
            first = ineligible_drivers[0]
            message = self.validation_logic.error_message_template.format(
                driver_name=first["driver_name"],
                status=first["status"],
            )

            return self.create_violation(
                message=message,
                details={
                    "ineligible_drivers": ineligible_drivers,
                    "allowed_statuses": allowed_statuses,
                    "ineligible_count": len(ineligible_drivers),
                },
            )

        return None
