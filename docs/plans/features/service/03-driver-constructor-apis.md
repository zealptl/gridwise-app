# Phase 1.3: Driver & Constructor APIs

## Overview
Implement CRUD endpoints for drivers and constructors with price history tracking.

**User Story:** N/A (Infrastructure for US-1.1, US-1.2, US-1.3)
**Epic:** Foundation
**Estimated Effort:** 4-6 hours

---

## Objectives

1. ✅ Create Driver API endpoints (GET, POST, PUT, DELETE)
2. ✅ Create Constructor API endpoints (GET, POST, PUT, DELETE)
3. ✅ Add price history tracking
4. ✅ Add filtering and pagination
5. ✅ Write unit and integration tests

---

## Files to Create/Modify

### 1. `service/app/schemas/driver.py`
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PriceHistory(BaseModel):
    price: float
    changed_at: datetime
    changed_by: str = "system"

class DriverBase(BaseModel):
    first_name: str
    last_name: str
    team_name: str
    nationality: str
    driver_number: int
    price: float
    status: str = "active"

class DriverCreate(DriverBase):
    pass

class DriverUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    team_name: Optional[str] = None
    nationality: Optional[str] = None
    driver_number: Optional[int] = None
    price: Optional[float] = None
    status: Optional[str] = None

class DriverResponse(DriverBase):
    driver_id: str
    price_history: List[PriceHistory] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 2. `service/app/schemas/constructor.py`
```python
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PriceHistory(BaseModel):
    price: float
    changed_at: datetime
    changed_by: str = "system"

class ConstructorBase(BaseModel):
    name: str
    full_name: str
    nationality: str
    price: float
    status: str = "active"

class ConstructorCreate(ConstructorBase):
    pass

class ConstructorUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    nationality: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None

class ConstructorResponse(ConstructorBase):
    constructor_id: str
    price_history: List[PriceHistory] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

### 3. `service/app/routers/drivers.py`
```python
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.get("/", response_model=List[DriverResponse])
async def get_all_drivers(
    team_name: Optional[str] = None,
    status: Optional[str] = Query(None, regex="^(active|inactive|reserve)$"),
    skip: int = 0,
    limit: int = 100
):
    """Get all drivers with optional filters"""
    query = {}

    if team_name:
        query["team_name"] = team_name
    if status:
        query["status"] = status

    drivers = await Driver.find(query).skip(skip).limit(limit).to_list()
    return drivers

@router.get("/{driver_id}", response_model=DriverResponse)
async def get_driver(driver_id: str):
    """Get a specific driver by ID"""
    driver = await Driver.find_one(Driver.driver_id == driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found"
        )
    return driver

@router.post("/", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
async def create_driver(driver_data: DriverCreate):
    """Create a new driver"""
    driver = Driver(**driver_data.dict())

    # Initialize price history
    driver.price_history = [{
        "price": driver.price,
        "changed_at": datetime.utcnow(),
        "changed_by": "system"
    }]

    await driver.insert()
    return driver

@router.put("/{driver_id}", response_model=DriverResponse)
async def update_driver(driver_id: str, driver_data: DriverUpdate):
    """Update an existing driver"""
    driver = await Driver.find_one(Driver.driver_id == driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found"
        )

    update_data = driver_data.dict(exclude_unset=True)

    # Track price changes
    if "price" in update_data and update_data["price"] != driver.price:
        driver.price_history.append({
            "price": update_data["price"],
            "changed_at": datetime.utcnow(),
            "changed_by": "admin"
        })

    # Update fields
    for field, value in update_data.items():
        setattr(driver, field, value)

    driver.updated_at = datetime.utcnow()
    await driver.save()
    return driver

@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_driver(driver_id: str):
    """Delete a driver (soft delete by setting status=inactive)"""
    driver = await Driver.find_one(Driver.driver_id == driver_id)
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Driver {driver_id} not found"
        )

    driver.status = "inactive"
    driver.updated_at = datetime.utcnow()
    await driver.save()

@router.get("/team/{team_name}", response_model=List[DriverResponse])
async def get_drivers_by_team(team_name: str):
    """Get all drivers for a specific team"""
    drivers = await Driver.find(Driver.team_name == team_name).to_list()
    if not drivers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No drivers found for team {team_name}"
        )
    return drivers
```

### 4. `service/app/routers/constructors.py`
```python
from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.models.constructor import Constructor
from app.schemas.constructor import ConstructorCreate, ConstructorUpdate, ConstructorResponse

router = APIRouter(prefix="/constructors", tags=["constructors"])

@router.get("/", response_model=List[ConstructorResponse])
async def get_all_constructors(
    status: Optional[str] = Query(None, regex="^(active|inactive)$"),
    skip: int = 0,
    limit: int = 100
):
    """Get all constructors with optional filters"""
    query = {}

    if status:
        query["status"] = status

    constructors = await Constructor.find(query).skip(skip).limit(limit).to_list()
    return constructors

@router.get("/{constructor_id}", response_model=ConstructorResponse)
async def get_constructor(constructor_id: str):
    """Get a specific constructor by ID"""
    constructor = await Constructor.find_one(Constructor.constructor_id == constructor_id)
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constructor {constructor_id} not found"
        )
    return constructor

@router.post("/", response_model=ConstructorResponse, status_code=status.HTTP_201_CREATED)
async def create_constructor(constructor_data: ConstructorCreate):
    """Create a new constructor"""
    constructor = Constructor(**constructor_data.dict())

    # Initialize price history
    constructor.price_history = [{
        "price": constructor.price,
        "changed_at": datetime.utcnow(),
        "changed_by": "system"
    }]

    await constructor.insert()
    return constructor

@router.put("/{constructor_id}", response_model=ConstructorResponse)
async def update_constructor(constructor_id: str, constructor_data: ConstructorUpdate):
    """Update an existing constructor"""
    constructor = await Constructor.find_one(Constructor.constructor_id == constructor_id)
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constructor {constructor_id} not found"
        )

    update_data = constructor_data.dict(exclude_unset=True)

    # Track price changes
    if "price" in update_data and update_data["price"] != constructor.price:
        constructor.price_history.append({
            "price": update_data["price"],
            "changed_at": datetime.utcnow(),
            "changed_by": "admin"
        })

    # Update fields
    for field, value in update_data.items():
        setattr(constructor, field, value)

    constructor.updated_at = datetime.utcnow()
    await constructor.save()
    return constructor

@router.delete("/{constructor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_constructor(constructor_id: str):
    """Delete a constructor (soft delete by setting status=inactive)"""
    constructor = await Constructor.find_one(Constructor.constructor_id == constructor_id)
    if not constructor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constructor {constructor_id} not found"
        )

    constructor.status = "inactive"
    constructor.updated_at = datetime.utcnow()
    await constructor.save()
```

---

## Implementation Steps

### Step 1: Create Schemas
1. Create `app/schemas/driver.py`
2. Create `app/schemas/constructor.py`

### Step 2: Create API Routers
1. Create `app/routers/drivers.py`
2. Create `app/routers/constructors.py`

### Step 3: Register Routers in Main App
Update `app/main.py`:
```python
from app.routers import drivers, constructors, rules

app.include_router(drivers.router, prefix=settings.API_V1_PREFIX)
app.include_router(constructors.router, prefix=settings.API_V1_PREFIX)
app.include_router(rules.router, prefix=settings.API_V1_PREFIX)
```

### Step 4: Write Tests
1. Create `tests/test_api/test_drivers.py`
2. Create `tests/test_api/test_constructors.py`

---

## Testing Strategy

### Integration Tests - `tests/test_api/test_drivers.py`
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_get_all_drivers():
    """Test getting all drivers"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/drivers")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 20  # From seed data

@pytest.mark.asyncio
async def test_get_driver_by_id():
    """Test getting a specific driver"""
    # First get all drivers to get a valid ID
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/drivers")
        drivers = response.json()
        driver_id = drivers[0]["driver_id"]

        # Get specific driver
        response = await client.get(f"/api/v1/drivers/{driver_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["driver_id"] == driver_id

@pytest.mark.asyncio
async def test_filter_drivers_by_team():
    """Test filtering drivers by team"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/drivers?team_name=Red Bull Racing")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Verstappen and Perez
        assert all(d["team_name"] == "Red Bull Racing" for d in data)

@pytest.mark.asyncio
async def test_update_driver_price_tracks_history():
    """Test that price changes are tracked in history"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Get a driver
        response = await client.get("/api/v1/drivers")
        driver = response.json()[0]
        driver_id = driver["driver_id"]
        original_price = driver["price"]

        # Update price
        new_price = original_price + 5.0
        response = await client.put(
            f"/api/v1/drivers/{driver_id}",
            json={"price": new_price}
        )
        assert response.status_code == 200
        updated_driver = response.json()

        assert updated_driver["price"] == new_price
        assert len(updated_driver["price_history"]) == 2
        assert updated_driver["price_history"][-1]["price"] == new_price
```

---

## Verification Checklist

- [ ] Can retrieve all drivers (GET /drivers)
- [ ] Can retrieve all constructors (GET /constructors)
- [ ] Can filter drivers by team
- [ ] Can filter by status (active/inactive)
- [ ] Can get single driver by ID
- [ ] Can get single constructor by ID
- [ ] Can create new driver
- [ ] Can create new constructor
- [ ] Can update driver (with price tracking)
- [ ] Can update constructor (with price tracking)
- [ ] Can soft-delete driver (sets status=inactive)
- [ ] Can soft-delete constructor (sets status=inactive)
- [ ] Price history appends correctly on price change
- [ ] Pagination works (skip/limit)
- [ ] 404 errors for non-existent IDs
- [ ] All tests pass

---

## Next Steps

After driver/constructor APIs are complete:
1. Proceed to Phase 2.1: Create Team (Backend)
2. Build team creation endpoint with rule validation
3. Integrate with rule engine
