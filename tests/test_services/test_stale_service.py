from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from ctm_app.models.template import Template
from ctm_app.models.user import User
from ctm_app.services.stale_service import get_stale_templates


def test_stale_published_template(db_session: Session, sample_user: User):
    stale_date = datetime.now(timezone.utc) - timedelta(days=400)
    t = Template(
        name="Stale NDA",
        template_type="NDA",
        owner_id=sample_user.id,
        status="published",
        current_version=1,
        review_interval_days=365,
        last_reviewed_at=stale_date,
    )
    db_session.add(t)
    db_session.commit()

    stale = get_stale_templates(db_session)
    assert len(stale) == 1
    assert stale[0]["days_overdue"] > 0


def test_fresh_published_template_not_stale(db_session: Session, sample_user: User):
    t = Template(
        name="Fresh NDA",
        template_type="NDA",
        owner_id=sample_user.id,
        status="published",
        current_version=1,
        review_interval_days=365,
        last_reviewed_at=datetime.now(timezone.utc),
    )
    db_session.add(t)
    db_session.commit()

    stale = get_stale_templates(db_session)
    assert len(stale) == 0


def test_draft_template_not_stale(db_session: Session, sample_user: User):
    t = Template(
        name="Draft NDA",
        template_type="NDA",
        owner_id=sample_user.id,
        status="draft",
        current_version=1,
    )
    db_session.add(t)
    db_session.commit()

    stale = get_stale_templates(db_session)
    assert len(stale) == 0
