from sqlalchemy import select
from sqlalchemy.orm import Session

from ctm_app.core.exceptions import VersionNotFoundError
from ctm_app.models.template import Template
from ctm_app.models.template_version import TemplateVersion
from ctm_app.models.user import User
from ctm_app.services.git_service import GitService


def create_version(
    db: Session,
    git_service: GitService,
    template: Template,
    file_content: bytes,
    filename: str,
    uploaded_by: User,
    change_summary: str | None = None,
) -> TemplateVersion:
    commit_sha = git_service.store_file(
        template_id=template.id,
        content=file_content,
        commit_message=f"Version {template.current_version} of {template.name}",
        author_name=uploaded_by.name,
    )

    version = TemplateVersion(
        template_id=template.id,
        version_number=template.current_version,
        filename=filename,
        git_commit_sha=commit_sha,
        change_summary=change_summary,
        uploaded_by_id=uploaded_by.id,
        file_size_bytes=len(file_content),
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version


def get_version(db: Session, template_id: str, version_number: int) -> TemplateVersion:
    stmt = select(TemplateVersion).where(
        TemplateVersion.template_id == template_id,
        TemplateVersion.version_number == version_number,
    )
    version = db.execute(stmt).scalar_one_or_none()
    if not version:
        raise VersionNotFoundError(
            f"Version {version_number} not found for template {template_id}"
        )
    return version


def list_versions(db: Session, template_id: str) -> list[TemplateVersion]:
    stmt = (
        select(TemplateVersion)
        .where(TemplateVersion.template_id == template_id)
        .order_by(TemplateVersion.version_number.desc())
    )
    return list(db.execute(stmt).scalars().all())


def download_version(
    git_service: GitService, template_id: str, commit_sha: str
) -> bytes:
    return git_service.retrieve_file(template_id, commit_sha)
