"""Persist conversations and chat messages."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_conversations"
down_revision: Union[str, None] = "0002_artifacts"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "aegis_conversations",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.String(length=120), nullable=False),
        sa.Column("owner_username", sa.String(length=120), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("classification", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    for name, column, unique in (
        ("ix_aegis_conversations_conversation_id", "conversation_id", True),
        ("ix_aegis_conversations_owner_username", "owner_username", False),
        ("ix_aegis_conversations_owner_user_id", "owner_user_id", False),
        ("ix_aegis_conversations_status", "status", False),
        ("ix_aegis_conversations_created_at", "created_at", False),
        ("ix_aegis_conversations_updated_at", "updated_at", False),
        ("ix_aegis_conversations_last_message_at", "last_message_at", False),
    ):
        op.create_index(name, "aegis_conversations", [column], unique=unique, if_not_exists=True)

    op.create_table(
        "aegis_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("message_id", sa.String(length=120), nullable=False),
        sa.Column("conversation_id", sa.String(length=120), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("agent_run_id", sa.String(length=120), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        if_not_exists=True,
    )
    for name, column, unique in (
        ("ix_aegis_messages_message_id", "message_id", True),
        ("ix_aegis_messages_conversation_id", "conversation_id", False),
        ("ix_aegis_messages_sequence", "sequence", False),
        ("ix_aegis_messages_status", "status", False),
        ("ix_aegis_messages_agent_run_id", "agent_run_id", False),
        ("ix_aegis_messages_created_at", "created_at", False),
    ):
        op.create_index(name, "aegis_messages", [column], unique=unique, if_not_exists=True)


def downgrade() -> None:
    op.drop_table("aegis_messages")
    op.drop_table("aegis_conversations")
