from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from app.auth import get_current_user
from app.models.constructor import Constructor
from app.schemas.constructor import ConstructorCreate, ConstructorUpdate, ConstructorResponse

router = APIRouter(prefix="/constructors", tags=["constructors"], dependencies=[Depends(get_current_user)])

@router.get("", response_model=List[ConstructorResponse])
async def get_all_constructors(
    status: Optional[str] = Query(None, pattern="^(active|inactive)$"),
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

@router.post("", response_model=ConstructorResponse, status_code=status.HTTP_201_CREATED)
async def create_constructor(constructor_data: ConstructorCreate):
    """Create a new constructor"""
    constructor = Constructor(**constructor_data.model_dump())

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

    update_data = constructor_data.model_dump(exclude_unset=True)

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
