from enum import StrEnum


class TemplateStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    PUBLISHED = "published"
    RETIRED = "retired"


class UserRole(StrEnum):
    DRAFTER = "drafter"
    REVIEWER = "reviewer"
    APPROVER = "approver"
    ADMIN = "admin"


VALID_TRANSITIONS: dict[tuple[TemplateStatus, TemplateStatus], set[UserRole]] = {
    (TemplateStatus.DRAFT, TemplateStatus.REVIEW): {UserRole.DRAFTER, UserRole.ADMIN},
    (TemplateStatus.REVIEW, TemplateStatus.DRAFT): {
        UserRole.REVIEWER,
        UserRole.APPROVER,
        UserRole.ADMIN,
    },
    (TemplateStatus.REVIEW, TemplateStatus.APPROVED): {
        UserRole.REVIEWER,
        UserRole.APPROVER,
        UserRole.ADMIN,
    },
    (TemplateStatus.APPROVED, TemplateStatus.REVIEW): {UserRole.APPROVER, UserRole.ADMIN},
    (TemplateStatus.APPROVED, TemplateStatus.PUBLISHED): {UserRole.APPROVER, UserRole.ADMIN},
    (TemplateStatus.PUBLISHED, TemplateStatus.RETIRED): {UserRole.APPROVER, UserRole.ADMIN},
    (TemplateStatus.RETIRED, TemplateStatus.DRAFT): {UserRole.APPROVER, UserRole.ADMIN},
}
