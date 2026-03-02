from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.workflow_states import TemplateStatus
from app.models.template import Template


def get_stale_templates(db: Session) -> list[dict]:
    now = datetime.now(UTC).replace(tzinfo=None)
    stmt = select(Template).where(Template.status == TemplateStatus.PUBLISHED)
    templates = list(db.execute(stmt).scalars().all())

    stale = []
    for t in templates:
        if t.last_reviewed_at is None:
            review_due = t.created_at + timedelta(days=t.review_interval_days)
            days_overdue = (now - review_due).days
            if days_overdue >= 0:
                stale.append({
                    "template": t,
                    "review_due_date": review_due,
                    "days_overdue": days_overdue,
                })
        else:
            last_reviewed = t.last_reviewed_at.replace(tzinfo=None) if t.last_reviewed_at.tzinfo else t.last_reviewed_at
            review_due = last_reviewed + timedelta(days=t.review_interval_days)
            days_overdue = (now - review_due).days
            if days_overdue > 0:
                stale.append({
                    "template": t,
                    "review_due_date": review_due,
                    "days_overdue": days_overdue,
                })

    return sorted(stale, key=lambda x: x["days_overdue"], reverse=True)
