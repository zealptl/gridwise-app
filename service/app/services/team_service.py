"""Team Service - Business logic for team management"""

from datetime import datetime
from typing import List

from fastapi import HTTPException, status

from app.models.constructor import Constructor
from app.models.driver import Driver
from app.models.team import ConstructorSelection, DriverSelection, FantasyTeam, TransferRecord
from app.models.validation import TeamValidationResult
from app.services.rule_engine import RuleEngine
from app.services.transfer_service import TransferService
from app.schemas.transfer import Change


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

    async def update_team(
        self,
        team_id: str,
        new_driver_ids: List[str],
        new_constructor_ids: List[str],
        new_drs_boost_driver_id: str,
    ) -> FantasyTeam:
        """
        Update team with transfer tracking and validation.

        Steps:
        1. Load existing team
        2. Calculate what changed
        3. Count transfers
        4. Calculate penalty
        5. Fetch new entity data
        6. Update team
        7. Recalculate budget
        8. Validate
        9. Record history
        10. Save

        Args:
            team_id: Team ID to update
            new_driver_ids: New list of 5 driver IDs
            new_constructor_ids: New list of 2 constructor IDs
            new_drs_boost_driver_id: Driver ID to assign DRS Boost

        Returns:
            Updated FantasyTeam

        Raises:
            HTTPException: If team not found, validation fails, or entities not found
        """
        # Step 1: Load existing team
        team = await FantasyTeam.find_one(FantasyTeam.team_id == team_id)
        if not team:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Team {team_id} not found",
            )

        # Step 2: Calculate changes
        old_driver_ids = [d.driver_id for d in team.drivers]
        old_constructor_ids = [c.constructor_id for c in team.constructors]

        changes = TransferService.calculate_changes(
            old_driver_ids=old_driver_ids,
            new_driver_ids=new_driver_ids,
            old_constructor_ids=old_constructor_ids,
            new_constructor_ids=new_constructor_ids,
        )

        # Step 3: Count transfers (driver/constructor swaps only)
        transfer_count = changes.get_transfer_count()

        # Step 4: Calculate penalty
        penalty = TransferService.calculate_transfer_penalty(
            transfers_used=transfer_count,
            available_transfers=team.available_transfers,
        )

        # Step 5: Fetch new entity data from database
        new_drivers_data = []
        for driver_id in new_driver_ids:
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

            new_drivers_data.append(
                DriverSelection(
                    driver_id=driver.driver_id,
                    driver_name=f"{driver.first_name} {driver.last_name}",
                    team_name=driver.team_name,
                    price=driver.price,
                )
            )

        new_constructors_data = []
        for constructor_id in new_constructor_ids:
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

            new_constructors_data.append(
                ConstructorSelection(
                    constructor_id=constructor.constructor_id,
                    constructor_name=constructor.name,
                    price=constructor.price,
                )
            )

        # Step 6: Update team composition
        team.drivers = new_drivers_data
        team.constructors = new_constructors_data
        team.drs_boost_driver_id = new_drs_boost_driver_id

        # Step 7: Recalculate budget
        team.calculate_budget()

        # Step 8: Validate against all rules
        validation_result = await self.validate_team(team, team.created_by)

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

        # Step 9: Record transfer history (only if transfers were made)
        if transfer_count > 0:
            # Build list of changes with details
            change_list = []

            # Drivers removed
            for driver_id in changes.drivers_removed:
                old_driver = next(
                    (d for d in [DriverSelection(driver_id=d.driver_id, driver_name=d.driver_name, team_name=d.team_name, price=d.price) for d in [dr for dr in [d for d in team.drivers if d.driver_id == driver_id]]] if True),
                    None
                )
                # Find from old team data
                for old_d in [d for d in old_driver_ids]:
                    if old_d == driver_id:
                        # Fetch driver details
                        driver = await Driver.find_one(Driver.driver_id == driver_id)
                        if driver:
                            change_list.append({
                                "type": "driver_out",
                                "entity_id": driver_id,
                                "entity_name": f"{driver.first_name} {driver.last_name}",
                                "price": driver.price,
                            })
                        break

            # Drivers added
            for driver_id in changes.drivers_added:
                driver = await Driver.find_one(Driver.driver_id == driver_id)
                if driver:
                    change_list.append({
                        "type": "driver_in",
                        "entity_id": driver_id,
                        "entity_name": f"{driver.first_name} {driver.last_name}",
                        "price": driver.price,
                    })

            # Constructors removed
            for constructor_id in changes.constructors_removed:
                constructor = await Constructor.find_one(Constructor.constructor_id == constructor_id)
                if constructor:
                    change_list.append({
                        "type": "constructor_out",
                        "entity_id": constructor_id,
                        "entity_name": constructor.name,
                        "price": constructor.price,
                    })

            # Constructors added
            for constructor_id in changes.constructors_added:
                constructor = await Constructor.find_one(Constructor.constructor_id == constructor_id)
                if constructor:
                    change_list.append({
                        "type": "constructor_in",
                        "entity_id": constructor_id,
                        "entity_name": constructor.name,
                        "price": constructor.price,
                    })

            transfer_record = TransferRecord(
                race_id=None,  # None for MVP
                transfers_used=transfer_count,
                transfers_available=team.available_transfers,
                penalty_points=penalty,
                changes=change_list,
                timestamp=datetime.utcnow(),
            )

            team.transfer_history.append(transfer_record)
            team.current_race_transfers = transfer_count

        # Step 10: Save and return
        team.is_valid = True
        team.last_validated_at = datetime.utcnow()
        team.updated_at = datetime.utcnow()
        await team.save()

        return team
