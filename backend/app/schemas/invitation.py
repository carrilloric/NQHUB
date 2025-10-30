"""Invitation Schemas"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, ConfigDict
from app.models.user import UserRole


class InvitationCreate(BaseModel):
    email: EmailStr | None = None
    role: UserRole = UserRole.TRADER


class InvitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    token: str
    email: str | None
    role: UserRole
    created_by_id: int | None
    used_by_id: int | None
    created_at: datetime
    used_at: datetime | None
    expires_at: datetime
    is_valid: bool
