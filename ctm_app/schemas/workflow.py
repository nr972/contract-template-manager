from datetime import datetime

from pydantic import BaseModel

from ctm_app.core.workflow_states import TemplateStatus


class WorkflowTransitionRequest(BaseModel):
    to_status: TemplateStatus
    comment: str | None = None


class WorkflowTransitionResponse(BaseModel):
    id: str
    template_id: str
    from_status: str
    to_status: str
    transitioned_by_id: str
    transitioned_by_name: str | None = None
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class AvailableTransitionsResponse(BaseModel):
    current_status: str
    available_transitions: list[str]
