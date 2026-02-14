"""Maximum Teams Per User Rule Validator"""

from typing import Optional

from app.models.team import FantasyTeam
from app.models.validation import RuleViolation
from app.services.rules.abstract_rule import AbstractRule


class MaxTeamsRule(AbstractRule):
    """
    Validates that a user hasn't exceeded the maximum number of active teams.

    Configuration:
        - max_teams: Maximum teams allowed per user (default: 5)

    Note: This rule requires additional context (user's team count) to be passed
    during validation, typically through the RuleEngine.
    """

    async def runRule(
        self,
        team: FantasyTeam,
        user_team_count: Optional[int] = None,
    ) -> Optional[RuleViolation]:
        """
        Check if user has exceeded max teams limit.

        Args:
            team: Fantasy team to validate
            user_team_count: Total active teams for this user

        Returns:
            RuleViolation if max teams exceeded, None otherwise
        """
        max_teams = self.config.get("max_teams", 5)

        # If user_team_count not provided, query it
        if user_team_count is None:
            user_team_count = await FantasyTeam.find(
                FantasyTeam.created_by == team.created_by,
                FantasyTeam.is_active == True,  # noqa: E712
                FantasyTeam.season == team.season,
            ).count()

        if user_team_count >= max_teams:
            message = self.validation_logic.error_message_template.format(
                actual=user_team_count,
                max_teams=max_teams,
            )

            return self.create_violation(
                message=message,
                details={
                    "user_id": team.created_by,
                    "active_team_count": user_team_count,
                    "max_teams": max_teams,
                    "overage": user_team_count - max_teams,
                },
            )

        return None
