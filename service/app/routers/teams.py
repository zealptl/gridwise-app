"""Teams Router - API endpoints for team management"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.auth import get_current_user
from app.models.team import FantasyTeam
from app.schemas.team import (
    PaginatedTeamsResponse,
    TeamCreate,
    TeamResponse,
    TeamSummary,
    TeamUpdate,
)
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["teams"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
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


@router.get("", response_model=PaginatedTeamsResponse)
async def get_all_teams(
    created_by: Optional[str] = Query(None, description="Filter by user ID"),
    season: Optional[int] = Query(None, description="Filter by season year"),
    is_valid: Optional[bool] = Query(None, description="Filter by validation status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Page size (max 100)"),
):
    """
    Get all teams with optional filtering and pagination.

    Filters:
    - created_by: Filter by user ID
    - season: Filter by season year
    - is_valid: Filter by validation status
    - is_active: Filter by active status

    Pagination:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 20, max: 100)

    Returns paginated list of teams with summary information.
    """
    # Build query filters
    query = {}

    if created_by:
        query["created_by"] = created_by

    if season is not None:
        query["season"] = season

    if is_valid is not None:
        query["is_valid"] = is_valid

    if is_active is not None:
        query["is_active"] = is_active

    # Get total count
    total_count = await FantasyTeam.find(query).count()

    # Query teams with pagination
    teams = (
        await FantasyTeam.find(query)
        .skip(skip)
        .limit(limit)
        .sort("-created_at")  # Most recent first
        .to_list()
    )

    # Transform to summary format
    teams_summary = [
        TeamSummary(
            team_id=team.team_id,
            team_name=team.team_name,
            season=team.season,
            budget_used=team.budget_used,
            budget_remaining=team.budget_remaining,
            is_valid=team.is_valid,
            driver_count=len(team.drivers),
            constructor_count=len(team.constructors),
            created_at=team.created_at,
            updated_at=team.updated_at,
        )
        for team in teams
    ]

    return PaginatedTeamsResponse(
        total=total_count,
        skip=skip,
        limit=limit,
        teams=teams_summary,
    )


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(team_id: str):
    """
    Get detailed information about a specific team.

    Args:
        team_id: Team ID

    Returns:
        Full team details including drivers, constructors, and validation status

    Raises:
        404: Team not found
    """
    team = await FantasyTeam.find_one(FantasyTeam.team_id == team_id)

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Team {team_id} not found",
        )

    return team


@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(team_id: str, team_data: TeamUpdate):
    """
    Update an existing fantasy team with transfer tracking.

    Tracks driver/constructor changes and calculates penalties:
    - Free transfers per race: 2
    - Penalty: -10 points per excess transfer
    - DRS Boost changes are free (don't count as transfers)

    Validates:
    - Exactly 5 drivers selected
    - Exactly 2 constructors selected
    - All entities are active
    - Budget cap not exceeded
    - DRS Boost assigned to one driver
    - All F1 Fantasy rules pass

    Returns the updated team with transfer history.

    Raises:
        404: Team not found
        422: Validation failed (with detailed violation info)
    """
    team_service = TeamService()

    team = await team_service.update_team(
        team_id=team_id,
        new_driver_ids=team_data.driver_ids,
        new_constructor_ids=team_data.constructor_ids,
        new_drs_boost_driver_id=team_data.drs_boost_driver_id,
    )

    return team
