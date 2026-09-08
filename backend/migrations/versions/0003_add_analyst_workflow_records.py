"""Add analyst notes, audit events, and IOC watchlist persistence.

Revision ID: 0003_add_analyst_workflow_records
Revises: 0002_create_user_profiles
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = "0003_analyst_workflow"
down_revision: str | None = "0002_create_user_profiles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "analyst_notes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("author_display_name", sa.String(length=120), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["author_user_id"], ["user_profiles.user_id"]),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyst_notes_case_id", "analyst_notes", ["case_id"], unique=False)
    op.create_index("ix_analyst_notes_author_user_id", "analyst_notes", ["author_user_id"], unique=False)
    op.create_index("ix_analyst_notes_created_at", "analyst_notes", ["created_at"], unique=False)

    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=48), nullable=False),
        sa.Column("resource_type", sa.String(length=48), nullable=False),
        sa.Column("resource_id", sa.String(length=128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_audit_events_actor_user_id", "audit_events", ["actor_user_id"], unique=False)
    op.create_index("ix_audit_events_action", "audit_events", ["action"], unique=False)
    op.create_index("ix_audit_events_resource_type", "audit_events", ["resource_type"], unique=False)
    op.create_index("ix_audit_events_resource_id", "audit_events", ["resource_id"], unique=False)
    op.create_index("ix_audit_events_timestamp", "audit_events", ["timestamp"], unique=False)

    op.create_table(
        "ioc_watchlist",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ioc_type", sa.String(length=32), nullable=False),
        sa.Column("normalized_value", sa.String(length=2048), nullable=False),
        sa.Column("created_by_user_id", sa.Uuid(), nullable=False),
        sa.Column("created_by_display_name", sa.String(length=120), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["user_profiles.user_id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ioc_type", "normalized_value", name="uq_ioc_watchlist_type_value"),
    )
    op.create_index("ix_ioc_watchlist_ioc_type", "ioc_watchlist", ["ioc_type"], unique=False)
    op.create_index("ix_ioc_watchlist_created_by_user_id", "ioc_watchlist", ["created_by_user_id"], unique=False)
    op.create_index("ix_ioc_watchlist_created_at", "ioc_watchlist", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ioc_watchlist_created_at", table_name="ioc_watchlist")
    op.drop_index("ix_ioc_watchlist_created_by_user_id", table_name="ioc_watchlist")
    op.drop_index("ix_ioc_watchlist_ioc_type", table_name="ioc_watchlist")
    op.drop_table("ioc_watchlist")
    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_id", table_name="audit_events")
    op.drop_index("ix_audit_events_resource_type", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_user_id", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_analyst_notes_created_at", table_name="analyst_notes")
    op.drop_index("ix_analyst_notes_author_user_id", table_name="analyst_notes")
    op.drop_index("ix_analyst_notes_case_id", table_name="analyst_notes")
    op.drop_table("analyst_notes")
