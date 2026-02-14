"""Budget Cap Rule Validator"""

from typing import Optional

from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class BudgetCapRule(AbstractRule):
    """
    Validates that team's total cost does not exceed the budget cap.

    Configuration:
        - max_budget: Maximum allowed budget (default: 100.0M)
    """

    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Check if team budget is within the cap.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if budget exceeded, None otherwise
        """
        max_budget = self.config.get("max_budget", 100.0)

        # Calculate team's total cost
        team.calculate_budget()

        if team.budget_used > max_budget:
            message = self.validation_logic.error_message_template.format(
                budget_used=team.budget_used,
                max_budget=max_budget,
            )

            return self.create_violation(
                message=message,
                details={
                    "budget_used": team.budget_used,
                    "budget_cap": max_budget,
                    "budget_remaining": team.budget_remaining,
                    "overage": team.budget_used - max_budget,
                },
            )

        return None
