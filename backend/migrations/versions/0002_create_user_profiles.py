"""Create backend-authorized cybersecurity user profiles.

Revision ID: 0002_create_user_profiles
Revises: 0001_create_cases
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0002_create_user_profiles"
down_revision: str | None = "0001_create_cases"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("organization", sa.String(length=160), nullable=True),
        sa.Column(
            "role",
            sa.String(length=32),
            server_default="ANALYST",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
    )
    op.create_index(
        "ix_user_profiles_email", "user_profiles", ["email"], unique=True
    )
    op.create_index(
        "ix_user_profiles_role", "user_profiles", ["role"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_user_profiles_role", table_name="user_profiles")
    op.drop_index("ix_user_profiles_email", table_name="user_profiles")
    op.drop_table("user_profiles")
