# Phase 1.2: Rule Management (Backend) - US-4.1

## Overview
Implement the flexible rule engine with CRUD APIs for managing F1 Fantasy game rules.

**User Story:** US-4.1 - As an admin, I want to configure game rules through a flexible rule engine
**Epic:** Epic 4 - Rule Management
**Estimated Effort:** 8-10 hours

---

## Objectives

1. ✅ Create Rule model with Beanie ODM
2. ✅ Build abstract base class for rule validators
3. ✅ Implement all 7 concrete rule classes
4. ✅ Create RuleEngine orchestrator class
5. ✅ Implement Rule CRUD API endpoints
6. ✅ Write comprehensive unit tests
7. ✅ Write integration tests

---

## Files to Create/Modify

### 1. `service/app/models/rule.py`
```python
from beanie import Document
from pydantic import Field, BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import uuid4
from enum import Enum

class RuleType(str, Enum):
    BUDGET_CAP = "budget_cap"
    ROSTER_SIZE = "roster_size"
    DRS_BOOST_REQUIRED = "drs_boost_required"
    MAX_TEAMS_PER_USER = "max_teams_per_user"
    TRANSFER_LIMIT = "transfer_limit"
    DRIVER_ELIGIBILITY = "driver_eligibility"

class RuleSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationLogic(BaseModel):
    operator: str  # "<=", "==", "in", "custom"
    field: str  # "budget_used", "len(drivers)", etc.
    threshold: str  # Reference to config value or literal
    error_message_template: str
    function: Optional[str] = None  # For custom validators

class Rule(Document):
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    rule_type: RuleType
    name: str
    description: str
    config: Dict[str, Any]  # Flexible configuration
    validation_logic: ValidationLogic
    severity: RuleSeverity = RuleSeverity.ERROR
    is_active: bool = True
    applies_to: str  # "team", "user", "driver"

    # Versioning (for future)
    effective_from: Optional[datetime] = None
    effective_until: Optional[datetime] = None

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = "system"

    class Settings:
        name = "rules"
        indexes = [
            "rule_id",
            "rule_type",
            "is_active"
        ]

    class Config:
        json_schema_extra = {
            "example": {
                "rule_type": "budget_cap",
                "name": "Budget Cap Rule",
                "description": "Total team cost must not exceed the cost cap",
                "config": {
                    "max_budget": 100.0,
                    "currency": "M"
                },
                "validation_logic": {
                    "operator": "<=",
                    "field": "budget_used",
                    "threshold": "config.max_budget",
                    "error_message_template": "Budget exceeded: {budget_used}M / {max_budget}M"
                },
                "severity": "error",
                "is_active": True,
                "applies_to": "team"
            }
        }
```

### 2. `service/app/models/validation.py`
```python
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    WARNING = "warning"

class RuleViolation(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    severity: str  # "error", "warning", "info"
    message: str
    details: Dict[str, Any]

class TeamValidationResult(BaseModel):
    team_id: str
    status: ValidationStatus
    is_valid: bool
    violations: List[RuleViolation] = []
    warnings: List[RuleViolation] = []
    info: List[RuleViolation] = []
    summary: Dict[str, Any]
```

### 3. `service/app/services/rules/abstract_rule.py`
```python
from abc import ABC, abstractmethod
from typing import Optional
from app.models.rule import Rule
from app.models.team import FantasyTeam
from app.models.validation import RuleViolation

class AbstractRule(ABC):
    """
    Abstract base class for all rule validators.
    Each rule type extends this class and implements its own runRule() method.
    """

    def __init__(self, rule: Rule):
        """Initialize rule with configuration from database."""
        self.rule_id = rule.rule_id
        self.rule_type = rule.rule_type
        self.name = rule.name
        self.description = rule.description
        self.config = rule.config
        self.validation_logic = rule.validation_logic
        self.severity = rule.severity
        self.is_active = rule.is_active
        self.applies_to = rule.applies_to

    @abstractmethod
    async def runRule(self, team: FantasyTeam) -> Optional[RuleViolation]:
        """
        Execute rule validation against a team.

        Args:
            team: Fantasy team to validate

        Returns:
            RuleViolation if validation fails, None if passes
        """
        pass

    def create_violation(self, message: str, details: dict) -> RuleViolation:
        """Helper method to create a RuleViolation object."""
        return RuleViolation(
            rule_id=self.rule_id,
            rule_name=self.name,
            rule_type=self.rule_type,
            severity=self.severity,
            message=message,
            details=details
        )
```

### 4. `service/app/services/rules/budget_cap_rule.py`
Full implementation as shown in the main plan.

### 5. `service/app/services/rules/roster_size_rule.py`
Full implementation as shown in the main plan.

### 6. `service/app/services/rules/drs_boost_rule.py`
Full implementation as shown in the main plan.

### 7. `service/app/services/rules/max_teams_rule.py`
Full implementation as shown in the main plan.

### 8. `service/app/services/rules/transfer_limit_rule.py`
Full implementation as shown in the main plan.

### 9. `service/app/services/rules/driver_eligibility_rule.py`
Full implementation as shown in the main plan.

### 10. `service/app/services/rule_engine.py`
Full RuleEngine orchestrator as shown in the main plan.

### 11. `service/app/routers/rules.py`
```python
from fastapi import APIRouter, HTTPException, status
from typing import List
from app.models.rule import Rule
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse

router = APIRouter(prefix="/rules", tags=["rules"])

@router.get("/", response_model=List[RuleResponse])
async def get_all_rules(
    is_active: Optional[bool] = None,
    rule_type: Optional[str] = None
):
    """Get all rules with optional filters"""
    query = {}
    if is_active is not None:
        query["is_active"] = is_active
    if rule_type:
        query["rule_type"] = rule_type

    rules = await Rule.find(query).to_list()
    return rules

@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """Get a specific rule by ID"""
    rule = await Rule.find_one(Rule.rule_id == rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )
    return rule

@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule_data: RuleCreate):
    """Create a new rule"""
    rule = Rule(**rule_data.dict())
    await rule.insert()
    return rule

@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, rule_data: RuleUpdate):
    """Update an existing rule"""
    rule = await Rule.find_one(Rule.rule_id == rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )

    # Update fields
    update_data = rule_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.updated_at = datetime.utcnow()
    await rule.save()
    return rule

@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str):
    """Delete a rule (soft delete by setting is_active=False)"""
    rule = await Rule.find_one(Rule.rule_id == rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )

    rule.is_active = False
    await rule.save()

@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(rule_id: str):
    """Toggle rule active status"""
    rule = await Rule.find_one(Rule.rule_id == rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found"
        )

    rule.is_active = not rule.is_active
    rule.updated_at = datetime.utcnow()
    await rule.save()
    return rule
```

### 12. `service/app/schemas/rule.py`
```python
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.rule import RuleType, RuleSeverity, ValidationLogic

class RuleBase(BaseModel):
    rule_type: RuleType
    name: str
    description: str
    config: Dict[str, Any]
    validation_logic: ValidationLogic
    severity: RuleSeverity = RuleSeverity.ERROR
    applies_to: str

class RuleCreate(RuleBase):
    is_active: bool = True

class RuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    validation_logic: Optional[ValidationLogic] = None
    severity: Optional[RuleSeverity] = None
    is_active: Optional[bool] = None

class RuleResponse(RuleBase):
    rule_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    created_by: str

    class Config:
        from_attributes = True
```

---

## Implementation Steps

### Step 1: Create Models
1. Create `app/models/rule.py`
2. Create `app/models/validation.py`
3. Update `app/database.py` to include Rule model

### Step 2: Create Rule Engine Classes
1. Create `app/services/rules/` directory
2. Create `abstract_rule.py`
3. Create all 6 concrete rule classes
4. Create `rule_engine.py` orchestrator

### Step 3: Create API Schemas
1. Create `app/schemas/rule.py`

### Step 4: Create API Router
1. Create `app/routers/rules.py`
2. Add router to main app

### Step 5: Write Unit Tests
1. Create `tests/test_rules/` directory
2. Test each rule class independently
3. Test rule engine with mock teams

### Step 6: Write Integration Tests
1. Test CRUD endpoints
2. Test rule validation with real teams

---

## Testing Strategy

### Unit Tests - `tests/test_rules/test_budget_cap_rule.py`
```python
import pytest
from app.services.rules.budget_cap_rule import BudgetCapRule
from app.models.rule import Rule
from app.models.team import FantasyTeam

@pytest.mark.asyncio
async def test_budget_cap_rule_passes():
    """Test budget cap rule passes when under limit"""
    rule_config = {
        "rule_type": "budget_cap",
        "name": "Budget Cap",
        "config": {"max_budget": 100.0},
        "validation_logic": {
            "operator": "<=",
            "field": "budget_used",
            "threshold": "config.max_budget",
            "error_message_template": "Budget exceeded"
        },
        "severity": "error",
        "is_active": True,
        "applies_to": "team"
    }

    rule = Rule(**rule_config)
    validator = BudgetCapRule(rule)

    team = FantasyTeam(budget_used=95.0, budget_cap=100.0)
    violation = await validator.runRule(team)

    assert violation is None

@pytest.mark.asyncio
async def test_budget_cap_rule_fails():
    """Test budget cap rule fails when over limit"""
    # Similar test but with budget_used=105.0
    # Assert violation is not None
    # Assert violation.severity == "error"
```

### Integration Tests - `tests/test_api/test_rules.py`
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_rule():
    """Test creating a new rule"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/rules", json={
            "rule_type": "budget_cap",
            "name": "Test Budget Cap",
            "description": "Test rule",
            "config": {"max_budget": 100.0},
            # ... rest of rule data
        })

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Budget Cap"
        assert "rule_id" in data
```

---

## Verification Checklist

- [ ] All 7 rule classes implement AbstractRule correctly
- [ ] RuleEngine can load rules from database
- [ ] RuleEngine.runRules() executes all active rules
- [ ] All CRUD endpoints work (GET, POST, PUT, DELETE, PATCH)
- [ ] Rule toggle endpoint works
- [ ] Unit tests pass for all rule classes (80%+ coverage)
- [ ] Integration tests pass for all API endpoints
- [ ] Can create, read, update, and delete rules via API
- [ ] Validation errors return proper structure

---

## Next Steps

After rule management is complete:
1. Proceed to Phase 1.3: Driver & Constructor APIs
2. Build CRUD endpoints for drivers and constructors
3. Set up foundation for team management
