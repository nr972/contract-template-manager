import json

from fastapi import APIRouter, Depends, Form, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session

from ctm_app.api.deps import get_current_user, get_db
from ctm_app.core.exceptions import FileValidationError, TemplateNotFoundError
from ctm_app.core.workflow_states import TemplateStatus
from ctm_app.models.template import Template
from ctm_app.models.user import User
from ctm_app.schemas.template import (
    TemplateListResponse,
    TemplateResponse,
    TemplateUpdate,
)
from ctm_app.services.file_validator import validate_docx_upload
from ctm_app.services.git_service import GitService
from ctm_app.services.template_service import (
    get_template_or_404,
    list_templates,
    template_to_response,
)
from ctm_app.services import stale_service, version_service

router = APIRouter(prefix="/templates", tags=["templates"])


def _get_git_service() -> GitService:
    return GitService()


@router.get("", response_model=TemplateListResponse)
def list_templates_endpoint(
    q: str | None = Query(None, description="Search name/description"),
    template_type: str | None = Query(None),
    status: str | None = Query(None),
    owner_id: str | None = Query(None),
    stale: bool | None = Query(None, description="Filter to stale templates only"),
    sort_by: str = Query("updated_at", pattern="^(name|updated_at|created_at)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> TemplateListResponse:
    if status and status not in list(TemplateStatus):
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    templates, total = list_templates(
        db, q=q, template_type=template_type, status=status,
        owner_id=owner_id, sort_by=sort_by, sort_order=sort_order,
        skip=skip, limit=limit,
    )

    responses = [template_to_response(t) for t in templates]
    if stale:
        responses = [r for r in responses if r.is_stale]
        total = len(responses)

    return TemplateListResponse(templates=responses, total=total, skip=skip, limit=limit)


@router.get("/stale")
def get_stale_templates(db: Session = Depends(get_db)) -> list[dict]:
    stale_list = stale_service.get_stale_templates(db)
    results = []
    for item in stale_list:
        resp = template_to_response(item["template"])
        results.append({
            **resp.model_dump(),
            "review_due_date": item["review_due_date"].isoformat() if item["review_due_date"] else None,
            "days_overdue": item["days_overdue"],
        })
    return results


@router.post("", response_model=TemplateResponse, status_code=201)
def create_template(
    file: UploadFile = File(...),
    metadata: str = Form(..., description="JSON string with template metadata"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    git_service: GitService = Depends(_get_git_service),
) -> TemplateResponse:
    try:
        meta = json.loads(metadata)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="metadata must be valid JSON")

    required_fields = {"name", "template_type"}
    missing = required_fields - set(meta.keys())
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required fields: {missing}")

    content = file.file.read()
    try:
        validate_docx_upload(file, content)
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    template = Template(
        name=meta["name"],
        description=meta.get("description"),
        template_type=meta["template_type"],
        use_case=meta.get("use_case"),
        owner_id=current_user.id,
        status=TemplateStatus.DRAFT,
        current_version=1,
        review_interval_days=meta.get("review_interval_days", 365),
    )
    db.add(template)
    db.flush()

    version_service.create_version(
        db=db,
        git_service=git_service,
        template=template,
        file_content=content,
        filename=file.filename or "template.docx",
        uploaded_by=current_user,
        change_summary="Initial version",
    )
    db.commit()
    db.refresh(template)
    return template_to_response(template)


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
) -> TemplateResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_to_response(template)


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    payload: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)

    db.commit()
    db.refresh(template)
    return template_to_response(template)


@router.delete("/{template_id}", response_model=TemplateResponse)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TemplateResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    template.status = TemplateStatus.RETIRED
    db.commit()
    db.refresh(template)
    return template_to_response(template)
