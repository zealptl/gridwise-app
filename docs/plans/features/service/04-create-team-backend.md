# Phase 2.1: Create Team (Backend) - US-1.2

## Overview
Implement POST /api/v1/teams endpoint with full rule validation and budget calculation.

**User Story:** US-1.2 - As a user, I want to create a new fantasy team
**Epic:** Epic 1 - Team Management
**Estimated Effort:** 6-8 hours

---

## Objectives

1. ✅ Create FantasyTeam model with all fields
2. ✅ Implement team creation endpoint
3. ✅ Integrate rule engine for validation
4. ✅ Calculate budget automatically
5. ✅ Handle DRS Boost selection
6. ✅ Return structured validation errors
7. ✅ Write comprehensive tests

---

## Files to Create/Modify

### 1. `service/app/models/team.py`
```python
from beanie import Document
from pydantic import Field, BaseModel
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class DriverSelection(BaseModel):
    driver_id: str
    driver_name: str
    team_name: str
    price: float

class ConstructorSelection(BaseModel):
    constructor_id: str
    constructor_name: str
    price: float

class TransferRecord(BaseModel):
    race_id: Optional[str] = None
    transfers_used: int
    transfers_available: int
    penalty_points: int
    changes: List[dict]
    timestamp: datetime

class FantasyTeam(Document):
    team_id: str = Field(default_factory=lambda: str(uuid4()))
    team_name: str
    created_by: str  # user_id

    # Season context
    season: int = 2026
    current_race_id: Optional[str] = None

    # Team composition
    drivers: List[DriverSelection] = Field(default_factory=list)
    constructors: List[ConstructorSelection] = Field(default_factory=list)

    # DRS Boost
    drs_boost_driver_id: Optional[str] = None

    # Budget tracking
    budget_cap: float = 100.0
    budget_used: float = 0.0
    budget_remaining: float = 100.0

    # Transfer tracking
    transfer_history: List[TransferRecord] = Field(default_factory=list)
    current_race_transfers: int = 0
    available_transfers: int = 2

    # Validation status
    is_valid: bool = False
    last_validated_at: Optional[datetime] = None
    validation_errors: List[dict] = Field(default_factory=list)

    # Metadata
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "teams"
        indexes = [
            "team_id",
            "created_by",
            "season",
            "is_valid",
            "is_active"
        ]

    def calculate_budget(self):
        """Calculate budget used and remaining"""
        total_drivers = sum(d.price for d in self.drivers)
        total_constructors = sum(c.price for c in self.constructors)
        self.budget_used = total_drivers + total_constructors
        self.budget_remaining = self.budget_cap - self.budget_used
```

### 2. `service/app/schemas/team.py`
```python
from pydantic import BaseModel, validator
from typing import List, Optional
from datetime import datetime

class DriverSelectionInput(BaseModel):
    driver_id: str

class ConstructorSelectionInput(BaseModel):
    constructor_id: str

class TeamCreate(BaseModel):
    team_name: str
    driver_ids: List[str]  # Exactly 5
    constructor_ids: List[str]  # Exactly 2
    drs_boost_driver_id: str
    season: int = 2026

    @validator('driver_ids')
    def validate_driver_count(cls, v):
        if len(v) != 5:
            raise ValueError('Must select exactly 5 drivers')
        if len(set(v)) != 5:
            raise ValueError('All drivers must be unique')
        return v

    @validator('constructor_ids')
    def validate_constructor_count(cls, v):
        if len(v) != 2:
            raise ValueError('Must select exactly 2 constructors')
        if len(set(v)) != 2:
            raise ValueError('All constructors must be unique')
        return v

    @validator('drs_boost_driver_id')
    def validate_drs_boost(cls, v, values):
        if 'driver_ids' in values and v not in values['driver_ids']:
            raise ValueError('DRS Boost must be assigned to one of the selected drivers')
        return v

class TeamResponse(BaseModel):
    team_id: str
    team_name: str
    created_by: str
    season: int
    drivers: List[dict]
    constructors: List[dict]
    drs_boost_driver_id: str
    budget_cap: float
    budget_used: float
    budget_remaining: float
    is_valid: bool
    validation_errors: List[dict]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 3. `service/app/services/team_service.py`
```python
from typing import List
from app.models.team import FantasyTeam, DriverSelection, ConstructorSelection
from app.models.driver import Driver
from app.models.constructor import Constructor
from app.models.rule import Rule
from app.models.validation import TeamValidationResult
from app.services.rule_engine import RuleEngine
from fastapi import HTTPException, status

class TeamService:
    """Business logic for team management"""

    async def create_team(
        self,
        team_name: str,
        driver_ids: List[str],
        constructor_ids: List[str],
        drs_boost_driver_id: str,
        created_by: str,
        season: int = 2026
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
                    detail=f"Driver {driver_id} not found"
                )

            if driver.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Driver {driver.first_name} {driver.last_name} is not active"
                )

            drivers_data.append(DriverSelection(
                driver_id=driver.driver_id,
                driver_name=f"{driver.first_name} {driver.last_name}",
                team_name=driver.team_name,
                price=driver.price
            ))

        # Fetch all constructors
        constructors_data = []
        for constructor_id in constructor_ids:
            constructor = await Constructor.find_one(
                Constructor.constructor_id == constructor_id
            )
            if not constructor:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Constructor {constructor_id} not found"
                )

            if constructor.status != "active":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Constructor {constructor.name} is not active"
                )

            constructors_data.append(ConstructorSelection(
                constructor_id=constructor.constructor_id,
                constructor_name=constructor.name,
                price=constructor.price
            ))

        # Create team instance
        team = FantasyTeam(
            team_name=team_name,
            created_by=created_by,
            season=season,
            drivers=drivers_data,
            constructors=constructors_data,
            drs_boost_driver_id=drs_boost_driver_id
        )

        # Calculate budget
        team.calculate_budget()

        # Validate team against rules
        validation_result = await self.validate_team(team)

        if not validation_result.is_valid:
            # Convert violations to error list
            team.validation_errors = [
                {
                    "rule_name": v.rule_name,
                    "message": v.message,
                    "severity": v.severity,
                    "details": v.details
                }
                for v in validation_result.violations
            ]

            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "code": "RULE_VIOLATION",
                    "message": "Team validation failed",
                    "violations": team.validation_errors
                }
            )

        # Mark as valid and save
        team.is_valid = True
        team.last_validated_at = datetime.utcnow()
        await team.insert()

        return team

    async def validate_team(self, team: FantasyTeam) -> TeamValidationResult:
        """
        Validate team against all active rules.

        Args:
            team: Team to validate

        Returns:
            TeamValidationResult with violations
        """
        # Get all active rules
        active_rules = await Rule.find(Rule.is_active == True).to_list()

        # Run validation
        rule_engine = RuleEngine()
        validation_result = await rule_engine.validate_team(team, active_rules)

        return validation_result
```

### 4. `service/app/routers/teams.py`
```python
from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from app.models.team import FantasyTeam
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
    """
    team_service = TeamService()

    # For MVP, use hardcoded user ID
    created_by = "admin-user-id"

    team = await team_service.create_team(
        team_name=team_data.team_name,
        driver_ids=team_data.driver_ids,
        constructor_ids=team_data.constructor_ids,
        drs_boost_driver_id=team_data.drs_boost_driver_id,
        created_by=created_by,
        season=team_data.season
    )

    return team
```

---

## Implementation Steps

### Step 1: Create Team Model
1. Create `app/models/team.py`
2. Add FantasyTeam to database initialization

### Step 2: Create Team Schemas
1. Create `app/schemas/team.py`

### Step 3: Create Team Service
1. Create `app/services/team_service.py`
2. Implement create_team method
3. Implement validate_team method

### Step 4: Create Team Router
1. Create `app/routers/teams.py`
2. Implement POST endpoint
3. Register router in main app

### Step 5: Write Tests
1. Create `tests/test_services/test_team_service.py`
2. Create `tests/test_api/test_teams_create.py`

---

## Testing Strategy

### Unit Tests - `tests/test_services/test_team_service.py`
```python
import pytest
from app.services.team_service import TeamService

@pytest.mark.asyncio
async def test_create_valid_team(seed_database):
    """Test creating a valid team passes validation"""
    service = TeamService()

    # Use seeded driver and constructor IDs
    team = await service.create_team(
        team_name="Test Team",
        driver_ids=["driver-1", "driver-2", "driver-3", "driver-4", "driver-5"],
        constructor_ids=["constructor-1", "constructor-2"],
        drs_boost_driver_id="driver-1",
        created_by="test-user",
        season=2026
    )

    assert team.is_valid
    assert team.budget_used <= 100.0
    assert len(team.drivers) == 5
    assert len(team.constructors) == 2

@pytest.mark.asyncio
async def test_create_team_budget_exceeded(seed_database):
    """Test creating team with budget exceeded fails"""
    service = TeamService()

    # Select most expensive drivers to exceed budget
    with pytest.raises(HTTPException) as exc:
        await service.create_team(
            team_name="Expensive Team",
            driver_ids=["verstappen", "leclerc", "hamilton", "norris", "alonso"],
            constructor_ids=["redbull", "ferrari"],
            drs_boost_driver_id="verstappen",
            created_by="test-user",
            season=2026
        )

    assert exc.value.status_code == 422
    assert "RULE_VIOLATION" in exc.value.detail["code"]
```

### Integration Tests - `tests/test_api/test_teams_create.py`
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_team_success(seed_database):
    """Test successful team creation"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get available drivers and constructors
        drivers_response = await client.get("/api/v1/drivers")
        drivers = drivers_response.json()[:5]

        constructors_response = await client.get("/api/v1/constructors")
        constructors = constructors_response.json()[:2]

        # Create team
        response = await client.post("/api/v1/teams", json={
            "team_name": "My Test Team",
            "driver_ids": [d["driver_id"] for d in drivers],
            "constructor_ids": [c["constructor_id"] for c in constructors],
            "drs_boost_driver_id": drivers[0]["driver_id"],
            "season": 2026
        })

        assert response.status_code == 201
        data = response.json()
        assert data["team_name"] == "My Test Team"
        assert data["is_valid"] == True
        assert len(data["drivers"]) == 5
        assert len(data["constructors"]) == 2

@pytest.mark.asyncio
async def test_create_team_budget_exceeded(seed_database):
    """Test team creation fails when budget exceeded"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Use expensive driver/constructor IDs that exceed 100M
        response = await client.post("/api/v1/teams", json={
            "team_name": "Too Expensive",
            "driver_ids": ["expensive-1", "expensive-2", ...],
            "constructor_ids": ["expensive-con-1", "expensive-con-2"],
            "drs_boost_driver_id": "expensive-1",
            "season": 2026
        })

        assert response.status_code == 422
        data = response.json()
        assert "RULE_VIOLATION" in data["detail"]["code"]
        assert any("budget" in v["message"].lower() for v in data["detail"]["violations"])
```

---

## Error Responses

### Budget Cap Violation
```json
{
  "detail": {
    "code": "RULE_VIOLATION",
    "message": "Team validation failed",
    "violations": [
      {
        "rule_name": "Budget Cap Rule",
        "message": "Budget exceeded: 105.5M / 100.0M",
        "severity": "error",
        "details": {
          "budget_used": 105.5,
          "budget_cap": 100.0,
          "overage": 5.5
        }
      }
    ]
  }
}
```

### Invalid Driver Count
```json
{
  "detail": [
    {
      "loc": ["body", "driver_ids"],
      "msg": "Must select exactly 5 drivers",
      "type": "value_error"
    }
  ]
}
```

---

## Verification Checklist

- [ ] Can create team with valid data
- [ ] Budget calculation is accurate
- [ ] Budget cap rule enforced
- [ ] Roster size rules enforced (5 drivers, 2 constructors)
- [ ] DRS Boost rule enforced (exactly 1 driver)
- [ ] Driver eligibility rule enforced (active status)
- [ ] Returns 422 with violations on validation failure
- [ ] Returns 201 with team data on success
- [ ] Team is saved to database
- [ ] All tests pass

---

## Next Steps

After team creation is complete:
1. Proceed to Phase 2.2: View Teams (Backend)
2. Implement GET endpoints for listing and viewing teams
