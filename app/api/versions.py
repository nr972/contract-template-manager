from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import FileValidationError, TemplateNotFoundError, VersionNotFoundError
from app.models.user import User
from app.schemas.template_version import VersionResponse
from app.services.file_validator import validate_docx_upload
from app.services.git_service import GitService
from app.services.template_service import get_template_or_404
from app.services import version_service

router = APIRouter(prefix="/templates/{template_id}/versions", tags=["versions"])


def _get_git_service() -> GitService:
    return GitService()


@router.get("", response_model=list[VersionResponse])
def list_versions(
    template_id: str,
    db: Session = Depends(get_db),
) -> list[VersionResponse]:
    try:
        get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    versions = version_service.list_versions(db, template_id)
    result = []
    for v in versions:
        resp = VersionResponse.model_validate(v)
        resp.uploaded_by_name = v.uploaded_by.name if v.uploaded_by else None
        result.append(resp)
    return result


@router.post("", response_model=VersionResponse, status_code=201)
def upload_version(
    template_id: str,
    file: UploadFile = File(...),
    change_summary: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    git_service: GitService = Depends(_get_git_service),
) -> VersionResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    content = file.file.read()
    try:
        validate_docx_upload(file, content)
    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))

    template.current_version += 1
    version = version_service.create_version(
        db=db,
        git_service=git_service,
        template=template,
        file_content=content,
        filename=file.filename or "template.docx",
        uploaded_by=current_user,
        change_summary=change_summary or None,
    )
    db.commit()
    db.refresh(version)

    resp = VersionResponse.model_validate(version)
    resp.uploaded_by_name = current_user.name
    return resp


@router.get("/{version_number}", response_model=VersionResponse)
def get_version(
    template_id: str,
    version_number: int,
    db: Session = Depends(get_db),
) -> VersionResponse:
    try:
        get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        version = version_service.get_version(db, template_id, version_number)
    except VersionNotFoundError:
        raise HTTPException(status_code=404, detail="Version not found")

    resp = VersionResponse.model_validate(version)
    resp.uploaded_by_name = version.uploaded_by.name if version.uploaded_by else None
    return resp


@router.get("/{version_number}/download")
def download_version(
    template_id: str,
    version_number: int,
    db: Session = Depends(get_db),
    git_service: GitService = Depends(_get_git_service),
) -> Response:
    try:
        get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        version = version_service.get_version(db, template_id, version_number)
    except VersionNotFoundError:
        raise HTTPException(status_code=404, detail="Version not found")

    try:
        file_bytes = version_service.download_version(
            git_service, template_id, version.git_commit_sha
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in repository")

    return Response(
        content=file_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{version.filename}"'},
    )
