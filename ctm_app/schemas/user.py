from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from ctm_app.core.workflow_states import UserRole


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., min_length=1, max_length=255)
    role: UserRole = UserRole.DRAFTER


class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
