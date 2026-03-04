from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ctm_app.api.deps import get_current_user, get_db
from ctm_app.core.exceptions import (
    InsufficientRoleError,
    InvalidTransitionError,
    TemplateNotFoundError,
)
from ctm_app.core.workflow_states import TemplateStatus, UserRole
from ctm_app.models.user import User
from ctm_app.models.workflow_transition import WorkflowTransition
from ctm_app.schemas.workflow import (
    AvailableTransitionsResponse,
    WorkflowTransitionRequest,
    WorkflowTransitionResponse,
)
from ctm_app.services.template_service import get_template_or_404
from ctm_app.services import workflow_service

router = APIRouter(prefix="/templates/{template_id}/workflow", tags=["workflow"])


@router.post("/transition", response_model=WorkflowTransitionResponse, status_code=201)
def transition_template(
    template_id: str,
    payload: WorkflowTransitionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkflowTransitionResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        record = workflow_service.transition(
            db=db,
            template=template,
            to_status=payload.to_status,
            user=current_user,
            comment=payload.comment,
        )
    except InvalidTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InsufficientRoleError as e:
        raise HTTPException(status_code=403, detail=str(e))

    resp = WorkflowTransitionResponse.model_validate(record)
    resp.transitioned_by_name = current_user.name
    return resp


@router.get("/history", response_model=list[WorkflowTransitionResponse])
def get_workflow_history(
    template_id: str,
    db: Session = Depends(get_db),
) -> list[WorkflowTransitionResponse]:
    try:
        get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    stmt = (
        select(WorkflowTransition)
        .where(WorkflowTransition.template_id == template_id)
        .order_by(WorkflowTransition.created_at.desc())
    )
    transitions = list(db.execute(stmt).scalars().all())
    result = []
    for t in transitions:
        resp = WorkflowTransitionResponse.model_validate(t)
        resp.transitioned_by_name = t.transitioned_by.name if t.transitioned_by else None
        result.append(resp)
    return result


@router.get("/available-transitions", response_model=AvailableTransitionsResponse)
def get_available_transitions(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AvailableTransitionsResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    available = workflow_service.get_available_transitions(
        TemplateStatus(template.status), UserRole(current_user.role)
    )
    return AvailableTransitionsResponse(
        current_status=template.status,
        available_transitions=[str(s) for s in available],
    )
