from datetime import UTC, datetime

from sqlalchemy.orm import Session

from ctm_app.core.exceptions import InsufficientRoleError, InvalidTransitionError
from ctm_app.core.workflow_states import (
    VALID_TRANSITIONS,
    TemplateStatus,
    UserRole,
)
from ctm_app.models.template import Template
from ctm_app.models.user import User
from ctm_app.models.workflow_transition import WorkflowTransition


def get_available_transitions(
    current_status: TemplateStatus, user_role: UserRole
) -> list[TemplateStatus]:
    available = []
    for (from_s, to_s), allowed_roles in VALID_TRANSITIONS.items():
        if from_s == current_status and UserRole(user_role) in allowed_roles:
            available.append(to_s)
    return available


def transition(
    db: Session,
    template: Template,
    to_status: TemplateStatus,
    user: User,
    comment: str | None = None,
) -> WorkflowTransition:
    from_status = TemplateStatus(template.status)
    key = (from_status, to_status)

    if key not in VALID_TRANSITIONS:
        raise InvalidTransitionError(
            f"Cannot transition from '{from_status}' to '{to_status}'"
        )

    allowed_roles = VALID_TRANSITIONS[key]
    if UserRole(user.role) not in allowed_roles:
        raise InsufficientRoleError(
            f"Role '{user.role}' cannot perform transition from '{from_status}' to '{to_status}'"
        )

    record = WorkflowTransition(
        template_id=template.id,
        from_status=from_status,
        to_status=to_status,
        transitioned_by_id=user.id,
        comment=comment,
    )
    db.add(record)

    template.status = to_status

    if to_status in (TemplateStatus.APPROVED, TemplateStatus.PUBLISHED):
        template.last_reviewed_at = datetime.now(UTC).replace(tzinfo=None)

    db.commit()
    db.refresh(record)
    return record
