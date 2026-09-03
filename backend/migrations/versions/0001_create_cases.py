"""Create the aggregate case-analysis table.

Revision ID: 0001_create_cases
Revises: None
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "0001_create_cases"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("email_sha256", sa.String(length=64), nullable=True),
        sa.Column("risk_score", sa.Integer(), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=True),
        sa.Column("analysis_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_cases_created_at", "cases", ["created_at"], unique=False)
    op.create_index("ix_cases_email_sha256", "cases", ["email_sha256"], unique=False)
    op.create_index("ix_cases_status", "cases", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_cases_status", table_name="cases")
    op.drop_index("ix_cases_email_sha256", table_name="cases")
    op.drop_index("ix_cases_created_at", table_name="cases")
    op.drop_table("cases")
