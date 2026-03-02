from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import TemplateNotFoundError, VersionNotFoundError
from app.schemas.diff import DiffResponse
from app.services import diff_service, version_service
from app.services.git_service import GitService
from app.services.template_service import get_template_or_404

router = APIRouter(prefix="/templates/{template_id}/diff", tags=["diff"])


def _get_git_service() -> GitService:
    return GitService()


@router.get("", response_model=DiffResponse)
def get_diff(
    template_id: str,
    from_version: int = Query(..., ge=1),
    to_version: int = Query(..., ge=1),
    db: Session = Depends(get_db),
    git_service: GitService = Depends(_get_git_service),
) -> DiffResponse:
    try:
        template = get_template_or_404(db, template_id)
    except TemplateNotFoundError:
        raise HTTPException(status_code=404, detail="Template not found")

    try:
        v_from = version_service.get_version(db, template_id, from_version)
        v_to = version_service.get_version(db, template_id, to_version)
    except VersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        bytes_from = version_service.download_version(
            git_service, template_id, v_from.git_commit_sha
        )
        bytes_to = version_service.download_version(
            git_service, template_id, v_to.git_commit_sha
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found in repository")

    text_from = diff_service.extract_text_from_docx(bytes_from)
    text_to = diff_service.extract_text_from_docx(bytes_to)

    diff_result = diff_service.compute_diff(
        text_from, text_to,
        label_a=f"Version {from_version}",
        label_b=f"Version {to_version}",
    )

    return DiffResponse(
        template_id=template_id,
        from_version=from_version,
        to_version=to_version,
        from_text=text_from,
        to_text=text_to,
        unified_diff=diff_result["unified_diff"],
        side_by_side=diff_result["side_by_side"],
    )
