"""Rule Management API Router"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import get_current_user
from app.models.rule import Rule, RuleType
from app.schemas.rule import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter(prefix="/rules", tags=["rules"], dependencies=[Depends(get_current_user)])


@router.get("/", response_model=List[RuleResponse])
async def get_all_rules(
    is_active: Optional[bool] = None,
    rule_type: Optional[RuleType] = None,
):
    """
    Get all rules with optional filters.

    Args:
        is_active: Filter by active status
        rule_type: Filter by rule type

    Returns:
        List of rules
    """
    query = {}

    if is_active is not None:
        query["is_active"] = is_active

    if rule_type:
        query["rule_type"] = rule_type

    rules = await Rule.find(query).to_list()
    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(rule_id: str):
    """
    Get a specific rule by ID.

    Args:
        rule_id: Rule ID

    Returns:
        Rule details

    Raises:
        404: Rule not found
    """
    rule = await Rule.find_one(Rule.rule_id == rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )

    return rule


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(rule_data: RuleCreate):
    """
    Create a new rule.

    Args:
        rule_data: Rule creation data

    Returns:
        Created rule

    Raises:
        400: Invalid rule data
    """
    rule = Rule(**rule_data.model_dump())
    await rule.insert()
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(rule_id: str, rule_data: RuleUpdate):
    """
    Update an existing rule.

    Args:
        rule_id: Rule ID
        rule_data: Rule update data

    Returns:
        Updated rule

    Raises:
        404: Rule not found
    """
    rule = await Rule.find_one(Rule.rule_id == rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )

    # Update fields
    update_data = rule_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)

    rule.updated_at = datetime.utcnow()
    await rule.save()

    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(rule_id: str):
    """
    Delete a rule (soft delete by setting is_active=False).

    Args:
        rule_id: Rule ID

    Raises:
        404: Rule not found
    """
    rule = await Rule.find_one(Rule.rule_id == rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )

    rule.is_active = False
    rule.updated_at = datetime.utcnow()
    await rule.save()


@router.patch("/{rule_id}/toggle", response_model=RuleResponse)
async def toggle_rule(rule_id: str):
    """
    Toggle rule active status.

    Args:
        rule_id: Rule ID

    Returns:
        Updated rule

    Raises:
        404: Rule not found
    """
    rule = await Rule.find_one(Rule.rule_id == rule_id)

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Rule {rule_id} not found",
        )

    rule.is_active = not rule.is_active
    rule.updated_at = datetime.utcnow()
    await rule.save()

    return rule
