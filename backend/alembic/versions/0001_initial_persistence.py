"""Create Aegis persistence tables.

Revision ID: 0001_initial_persistence
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_persistence"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aegis_users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("clearance_tags", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_aegis_users_username", "aegis_users", ["username"], unique=True, if_not_exists=True)

    op.create_table(
        "aegis_agent_runs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("run_id", sa.String(length=120), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=False),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column("model_id", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=48), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("final_result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_aegis_agent_runs_run_id", "aegis_agent_runs", ["run_id"], unique=True, if_not_exists=True)
    op.create_index("ix_aegis_agent_runs_user_id", "aegis_agent_runs", ["user_id"], unique=False, if_not_exists=True)
    op.create_index("ix_aegis_agent_runs_username", "aegis_agent_runs", ["username"], unique=False, if_not_exists=True)
    op.create_index("ix_aegis_agent_runs_status", "aegis_agent_runs", ["status"], unique=False, if_not_exists=True)

    op.create_table(
        "aegis_audit_records",
        sa.Column("id", sa.String(length=120), nullable=False),
        sa.Column("timestamp", sa.String(length=64), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("username", sa.String(length=120), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("run_id", sa.String(length=120), nullable=True),
        sa.Column("clearance_tags", sa.JSON(), nullable=False),
        sa.Column("query_or_action", sa.Text(), nullable=False),
        sa.Column("diagnosis_summary", sa.Text(), nullable=False),
        sa.Column("citations_count", sa.Integer(), nullable=False),
        sa.Column("hitl_approval_required", sa.Boolean(), nullable=False),
        sa.Column("equipment_tag", sa.String(length=160), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("previous_hash", sa.String(length=128), nullable=False),
        sa.Column("entry_hash", sa.String(length=128), nullable=False),
        sa.Column("integrity_hash", sa.String(length=128), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    for name, column in (
        ("ix_aegis_audit_records_timestamp", "timestamp"),
        ("ix_aegis_audit_records_event_type", "event_type"),
        ("ix_aegis_audit_records_username", "username"),
        ("ix_aegis_audit_records_user_id", "user_id"),
        ("ix_aegis_audit_records_run_id", "run_id"),
        ("ix_aegis_audit_records_entry_hash", "entry_hash"),
    ):
        op.create_index(name, "aegis_audit_records", [column], if_not_exists=True)


def downgrade() -> None:
    op.drop_table("aegis_audit_records")
    op.drop_table("aegis_agent_runs")
    op.drop_table("aegis_users")
