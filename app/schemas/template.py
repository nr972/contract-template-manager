from datetime import datetime

from pydantic import BaseModel, Field

from app.core.workflow_states import TemplateStatus


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    template_type: str = Field(..., min_length=1, max_length=100)
    use_case: str | None = Field(None, max_length=255)
    review_interval_days: int = Field(365, ge=1, le=3650)


class TemplateUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    template_type: str | None = Field(None, min_length=1, max_length=100)
    use_case: str | None = Field(None, max_length=255)
    review_interval_days: int | None = Field(None, ge=1, le=3650)


class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str | None
    template_type: str
    use_case: str | None
    owner_id: str
    owner_name: str | None = None
    status: str
    current_version: int
    review_interval_days: int
    last_reviewed_at: datetime | None
    is_stale: bool = False
    days_until_review_due: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]
    total: int
    skip: int
    limit: int
