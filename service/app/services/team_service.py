"""Team Service - Business logic for team management"""

from datetime import datetime
from typing import List

from fastapi import HTTPException, status

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam
from app.models.validation import TeamValidationResult
from app.services.rule_engine import RuleEngine


class TeamService:
    """Business logic for team management"""

    async def create_team(
        self,
        team_name: str,
        driver_ids: List[str],
        constructor_ids: List[str],
        drs_boost_driver_id: str,
        created_by: str,
        season: int = 2026,
    ) -> FantasyTeam:
        """
        Create a new fantasy team with validation.

        Args:
            team_name: Name for the team
            driver_ids: List of 5 driver IDs
            constructor_ids: List of 2 constructor IDs
            drs_boost_driver_id: Driver ID to assign DRS Boost
            created_by: User ID creating the team
            season: Season year

        Returns:
            Created FantasyTeam

        Raises:
            HTTPException: If validation fails or entities not found
        """

        # Fetch all drivers
        drivers_data = []
        for driver_id in driver_ids:
            driver = await Driver.find_one(Driver.driver_id == driver_id)
            if not driver:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Driver {driver_id} not found",
                )

            if driver.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver {driver.first_name} {driver.last_name} is not active",
                )

            drivers_data.append(
                DriverSelection(
                    driver_id=driver.driver_id,
                    driver_name=f"{driver.first_name} {driver.last_name}",
                    team_name=driver.team_name,
                    price=driver.price,
                )
            )

        # Fetch all constructors
        constructors_data = []
        for constructor_id in constructor_ids:
            constructor = await Constructor.find_one(
                Constructor.constructor_id == constructor_id
            )
            if not constructor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Constructor {constructor_id} not found",
                )

            if constructor.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Constructor {constructor.name} is not active",
                )

            constructors_data.append(
                ConstructorSelection(
                    constructor_id=constructor.constructor_id,
                    constructor_name=constructor.name,
                    price=constructor.price,
                )
            )

        # Create team instance
        team = FantasyTeam(
            team_name=team_name,
            created_by=created_by,
            season=season,
            drivers=drivers_data,
            constructors=constructors_data,
            drs_boost_driver_id=drs_boost_driver_id,
        )

        # Calculate budget
        team.calculate_budget()

        # Validate team against rules
        validation_result = await self.validate_team(team, created_by)

        if not validation_result.is_valid:
            # Convert violations to error list
            team.validation_errors = [
                {
                    "rule_name": v.rule_name,
                    "message": v.message,
                    "severity": v.severity,
                    "details": v.details,
                }
                for v in validation_result.violations
            ]

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "RULE_VIOLATION",
                    "message": "Team validation failed",
                    "violations": team.validation_errors,
                },
            )

        # Mark as valid and save
        team.is_valid = True
        team.last_validated_at = datetime.utcnow()
        await team.insert()

        return team

    async def validate_team(
        self, team: FantasyTeam, created_by: str
    ) -> TeamValidationResult:
        """
        Validate team against all active rules.

        Args:
            team: Team to validate
            created_by: User ID creating the team (for max teams rule)

        Returns:
            TeamValidationResult with violations
        """
        # Create rule engine and load active rules
        rule_engine = RuleEngine()
        await rule_engine.load_rules()

        # Count existing teams for this user (for max teams rule)
        user_team_count = await FantasyTeam.find(
            FantasyTeam.created_by == created_by,
            FantasyTeam.is_active == True,
            FantasyTeam.season == team.season,
        ).count()

        # Run validation
        validation_result = await rule_engine.validate_team(
            team, user_team_count=user_team_count
        )

        return validation_result
