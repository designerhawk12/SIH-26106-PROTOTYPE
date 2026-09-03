"""Simple, extensible application permission mapping."""

from ...schemas import Permission, UserRole

ANALYST_PERMISSIONS = frozenset(
    {
        Permission.ANALYZE_EMAILS,
        Permission.INSPECT_CASES,
        Permission.GENERATE_REPORTS,
        Permission.EXPORT_EVIDENCE,
        Permission.CREATE_ANALYST_NOTES,
    }
)

ROLE_PERMISSIONS: dict[UserRole, frozenset[Permission]] = {
    UserRole.ANALYST: ANALYST_PERMISSIONS,
    UserRole.SENIOR_ANALYST: ANALYST_PERMISSIONS
    | {Permission.REVIEW_CASES, Permission.ACCESS_CAMPAIGNS},
    UserRole.ADMIN: frozenset(Permission),
}


def permissions_for_role(role: UserRole) -> tuple[Permission, ...]:
    return tuple(sorted(ROLE_PERMISSIONS[role], key=str))


def role_has_permission(role: UserRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]
