from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate, DriverResponse

router = APIRouter(prefix="/drivers", tags=["drivers"])

@router.get("/", response_model=List[DriverResponse])
async def get_all_drivers(
    team_name: Optional[str] = None,
    status: Optional[str] = Query(None, pattern="^(active|inactive|reserve)$"),
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
    driver = Driver(**driver_data.model_dump())

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

    update_data = driver_data.model_dump(exclude_unset=True)

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
