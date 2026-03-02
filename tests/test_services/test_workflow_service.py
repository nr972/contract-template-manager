import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientRoleError, InvalidTransitionError
from app.core.workflow_states import TemplateStatus, UserRole
from app.models.template import Template
from app.models.user import User
from app.services import workflow_service


def _make_template(db: Session, user: User, status: str = "draft") -> Template:
    t = Template(
        name="Test",
        template_type="NDA",
        owner_id=user.id,
        status=status,
        current_version=1,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def test_valid_transition(db_session: Session, sample_user):
    template = _make_template(db_session, sample_user)
    record = workflow_service.transition(
        db_session, template, TemplateStatus.REVIEW, sample_user
    )
    assert record.to_status == "review"
    assert template.status == "review"


def test_invalid_transition(db_session: Session, sample_user):
    template = _make_template(db_session, sample_user)
    with pytest.raises(InvalidTransitionError):
        workflow_service.transition(
            db_session, template, TemplateStatus.PUBLISHED, sample_user
        )


def test_insufficient_role(db_session: Session, sample_user, reviewer_user):
    template = _make_template(db_session, sample_user)
    workflow_service.transition(db_session, template, TemplateStatus.REVIEW, sample_user)
    workflow_service.transition(db_session, template, TemplateStatus.APPROVED, reviewer_user)
    # Drafter can't publish
    with pytest.raises(InsufficientRoleError):
        workflow_service.transition(
            db_session, template, TemplateStatus.PUBLISHED, sample_user
        )


def test_approval_sets_last_reviewed(db_session: Session, sample_user, reviewer_user):
    template = _make_template(db_session, sample_user)
    assert template.last_reviewed_at is None
    workflow_service.transition(db_session, template, TemplateStatus.REVIEW, sample_user)
    workflow_service.transition(db_session, template, TemplateStatus.APPROVED, reviewer_user)
    assert template.last_reviewed_at is not None


def test_get_available_transitions():
    available = workflow_service.get_available_transitions(
        TemplateStatus.DRAFT, UserRole.DRAFTER
    )
    assert TemplateStatus.REVIEW in available
    assert TemplateStatus.PUBLISHED not in available
