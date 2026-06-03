"""Auth router — user registration with Cognito."""

import logging
import os

import boto3
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register", status_code=201)
async def register(request: RegisterRequest):
    """Register a new user and set custom:tier = free in Cognito."""
    from app.config import settings

    cognito = boto3.client("cognito-idp", region_name=AWS_REGION)
    try:
        resp = cognito.sign_up(
            ClientId=settings.COGNITO_APP_CLIENT_ID,
            Username=request.email,
            Password=request.password,
            UserAttributes=[{"Name": "email", "Value": request.email}],
        )
        user_sub = resp["UserSub"]

        cognito.admin_update_user_attributes(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=request.email,
            UserAttributes=[{"Name": "custom:tier", "Value": "free"}],
        )

        return {"user_id": user_sub, "email": request.email, "tier": "free"}
    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(status_code=409, detail="Email already registered")
    except cognito.exceptions.InvalidPasswordException as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Registration failed: %s", exc)
        raise HTTPException(status_code=500, detail="Registration failed")
