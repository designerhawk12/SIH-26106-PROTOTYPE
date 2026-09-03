"""Authentication, profile, and authorization contracts."""

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import Field, field_validator

from .email import ContractModel


class UserRole(StrEnum):
    ANALYST = "ANALYST"
    SENIOR_ANALYST = "SENIOR_ANALYST"
    ADMIN = "ADMIN"


class Permission(StrEnum):
    ANALYZE_EMAILS = "ANALYZE_EMAILS"
    INSPECT_CASES = "INSPECT_CASES"
    GENERATE_REPORTS = "GENERATE_REPORTS"
    EXPORT_EVIDENCE = "EXPORT_EVIDENCE"
    CREATE_ANALYST_NOTES = "CREATE_ANALYST_NOTES"
    REVIEW_CASES = "REVIEW_CASES"
    ACCESS_CAMPAIGNS = "ACCESS_CAMPAIGNS"
    MANAGE_USERS = "MANAGE_USERS"
    VIEW_SYSTEM_CONFIGURATION = "VIEW_SYSTEM_CONFIGURATION"


class UserProfile(ContractModel):
    user_id: UUID
    display_name: str
    email: str
    organization: str | None = None
    role: UserRole
    permissions: tuple[Permission, ...] = ()
    created_at: datetime
    updated_at: datetime


class UpdateProfileRequest(ContractModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    organization: str | None = Field(default=None, max_length=160)


class UpdateRoleRequest(ContractModel):
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def parse_json_role(cls, value: object) -> object:
        """Accept the wire-format enum string while keeping contracts strict."""

        return UserRole(value) if isinstance(value, str) else value


class UserListResponse(ContractModel):
    items: tuple[UserProfile, ...] = ()
