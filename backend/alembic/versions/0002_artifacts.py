"""Add controlled report artifacts."""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_artifacts"
down_revision: Union[str, None] = "0001_initial_persistence"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aegis_artifacts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("artifact_id", sa.String(length=120), nullable=False),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("format", sa.String(length=8), nullable=False),
        sa.Column("storage_name", sa.String(length=180), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("agent_run_id", sa.String(length=120), nullable=True),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("source_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("audit_reference", sa.String(length=120), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    op.create_index("ix_aegis_artifacts_artifact_id", "aegis_artifacts", ["artifact_id"], unique=True, if_not_exists=True)
    op.create_index("ix_aegis_artifacts_storage_name", "aegis_artifacts", ["storage_name"], unique=True, if_not_exists=True)
    op.create_index("ix_aegis_artifacts_created_by", "aegis_artifacts", ["created_by"], unique=False, if_not_exists=True)
    op.create_index("ix_aegis_artifacts_agent_run_id", "aegis_artifacts", ["agent_run_id"], unique=False, if_not_exists=True)
    op.create_index("ix_aegis_artifacts_status", "aegis_artifacts", ["status"], unique=False, if_not_exists=True)


def downgrade() -> None:
    op.drop_table("aegis_artifacts")
