from datetime import UTC, datetime, timedelta

from sqlalchemy import select, func, or_
from sqlalchemy.orm import Session

from ctm_app.core.exceptions import TemplateNotFoundError
from ctm_app.core.workflow_states import TemplateStatus
from ctm_app.models.template import Template
from ctm_app.models.user import User
from ctm_app.schemas.template import TemplateResponse


def get_template_or_404(db: Session, template_id: str) -> Template:
    template = db.get(Template, template_id)
    if not template:
        raise TemplateNotFoundError(f"Template {template_id} not found")
    return template


def compute_stale_fields(template: Template) -> dict:
    now = datetime.now(UTC).replace(tzinfo=None)
    is_stale = False
    days_until_review_due = None

    if template.status == TemplateStatus.PUBLISHED:
        if template.last_reviewed_at is None:
            is_stale = True
            days_until_review_due = -(
                (now - template.created_at).days - template.review_interval_days
            )
        else:
            last_reviewed = template.last_reviewed_at.replace(tzinfo=None) if template.last_reviewed_at.tzinfo else template.last_reviewed_at
            review_due = last_reviewed + timedelta(days=template.review_interval_days)
            days_until_review_due = (review_due - now).days
            is_stale = days_until_review_due < 0

    return {"is_stale": is_stale, "days_until_review_due": days_until_review_due}


def template_to_response(template: Template) -> TemplateResponse:
    stale = compute_stale_fields(template)
    owner_name = template.owner.name if template.owner else None
    return TemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        template_type=template.template_type,
        use_case=template.use_case,
        owner_id=template.owner_id,
        owner_name=owner_name,
        status=template.status,
        current_version=template.current_version,
        review_interval_days=template.review_interval_days,
        last_reviewed_at=template.last_reviewed_at,
        is_stale=stale["is_stale"],
        days_until_review_due=stale["days_until_review_due"],
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


def list_templates(
    db: Session,
    q: str | None = None,
    template_type: str | None = None,
    status: str | None = None,
    owner_id: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Template], int]:
    stmt = select(Template)

    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Template.name.ilike(pattern), Template.description.ilike(pattern)))
    if template_type:
        stmt = stmt.where(Template.template_type == template_type)
    if status:
        stmt = stmt.where(Template.status == status)
    if owner_id:
        stmt = stmt.where(Template.owner_id == owner_id)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = db.execute(count_stmt).scalar() or 0

    sort_col = getattr(Template, sort_by, Template.updated_at)
    if sort_order == "asc":
        stmt = stmt.order_by(sort_col.asc())
    else:
        stmt = stmt.order_by(sort_col.desc())

    stmt = stmt.offset(skip).limit(limit)
    templates = list(db.execute(stmt).scalars().all())
    return templates, total
