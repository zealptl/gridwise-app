"""User Model"""

from datetime import datetime
from uuid import uuid4

from beanie import Document
from pydantic import Field


class User(Document):
    """User document model"""

    user_id: str = Field(default_factory=lambda: str(uuid4()))
    username: str
    email: str

    # For MVP - single user mode, no password needed
    is_active: bool = True
    is_admin: bool = True

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        indexes = [
            "user_id",
            "username",
            "email",
        ]
