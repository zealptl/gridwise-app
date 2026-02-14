"""Transfer Limit Rule Validator"""

from typing import Optional

from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class TransferLimitRule(AbstractRule):
    """
    Validates transfer limits and calculates penalty points.

    Configuration:
        - free_transfers_per_race: Number of free transfers allowed (default: 2)
        - penalty_points_per_transfer: Penalty points for each excess transfer (default: 4)
    """

    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Check transfer limits and calculate penalties.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation (warning) if free transfers exceeded, None otherwise
        """
        free_transfers = self.config.get("free_transfers_per_race", 2)
        penalty_per_transfer = self.config.get("penalty_points_per_transfer", 4)

        transfers_this_race = team.current_race_transfers

        if transfers_this_race > free_transfers:
            excess_transfers = transfers_this_race - free_transfers
            penalty_points = excess_transfers * penalty_per_transfer

            message = self.validation_logic.error_message_template.format(
                transfers_this_race=transfers_this_race,
                free_transfers_per_race=free_transfers,
                penalty_points=penalty_points,
            )

            return self.create_violation(
                message=message,
                details={
                    "transfers_this_race": transfers_this_race,
                    "free_transfers": free_transfers,
                    "excess_transfers": excess_transfers,
                    "penalty_points_per_transfer": penalty_per_transfer,
                    "total_penalty_points": penalty_points,
                },
            )

        return None
