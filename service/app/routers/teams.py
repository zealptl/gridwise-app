"""Teams Router - API endpoints for team management"""

from fastapi import APIRouter, status

from app.schemas.team import TeamCreate, TeamResponse
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("/", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(team_data: TeamCreate):
    """
    Create a new fantasy team.

    Validates:
    - Exactly 5 drivers selected
    - Exactly 2 constructors selected
    - All entities are active
    - Budget cap not exceeded
    - DRS Boost assigned to one driver
    - All F1 Fantasy rules pass

    Returns the created team with validation status.
    """
    team_service = TeamService()

    # For MVP, use hardcoded user ID
    # TODO: Replace with actual authenticated user ID when auth is implemented
    created_by = "admin-user-id"

    team = await team_service.create_team(
        team_name=team_data.team_name,
        driver_ids=team_data.driver_ids,
        constructor_ids=team_data.constructor_ids,
        drs_boost_driver_id=team_data.drs_boost_driver_id,
        created_by=created_by,
        season=team_data.season,
    )

    return team
