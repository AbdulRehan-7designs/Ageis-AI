from datetime import datetime, timezone
from typing import Any

from sqlalchemy import DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserRecord(Base):
    __tablename__ = "aegis_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(512))
    role: Mapped[str] = mapped_column(String(32))
    clearance_tags: Mapped[list[str]] = mapped_column(JSON)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class AgentRunRecord(Base):
    __tablename__ = "aegis_agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    run_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    username: Mapped[str] = mapped_column(String(120), index=True)
    task: Mapped[str] = mapped_column(Text)
    model_id: Mapped[str] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(48), index=True)
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSON, default=list)
    final_result: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class ConversationRecord(Base):
    __tablename__ = "aegis_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    owner_username: Mapped[str] = mapped_column(String(120), index=True)
    owner_user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(240), default="New conversation")
    classification: Mapped[str] = mapped_column(String(32), default="INTERNAL")
    status: Mapped[str] = mapped_column(String(32), default="ACTIVE", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        index=True,
    )
    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class MessageRecord(Base):
    __tablename__ = "aegis_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    conversation_id: Mapped[str] = mapped_column(String(120), index=True)
    role: Mapped[str] = mapped_column(String(32))
    content: Mapped[str] = mapped_column(Text)
    sequence: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(32), default="COMPLETED", index=True)
    agent_run_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True
    )


class AuditRecord(Base):
    __tablename__ = "aegis_audit_records"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    timestamp: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    username: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    clearance_tags: Mapped[list[str]] = mapped_column(JSON)
    query_or_action: Mapped[str] = mapped_column(Text)
    diagnosis_summary: Mapped[str] = mapped_column(Text)
    citations_count: Mapped[int] = mapped_column(Integer, default=0)
    hitl_approval_required: Mapped[bool] = mapped_column(default=False)
    equipment_tag: Mapped[str] = mapped_column(String(160), default="N/A")
    status: Mapped[str] = mapped_column(String(64), default="LOGGED")
    previous_hash: Mapped[str] = mapped_column(String(128))
    entry_hash: Mapped[str] = mapped_column(String(128), index=True)
    integrity_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class ArtifactRecord(Base):
    __tablename__ = "aegis_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    artifact_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    report_type: Mapped[str] = mapped_column(String(64))
    format: Mapped[str] = mapped_column(String(8))
    storage_name: Mapped[str] = mapped_column(String(180), unique=True)
    created_by: Mapped[str] = mapped_column(String(120), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    agent_run_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    classification: Mapped[str] = mapped_column(String(32))
    source_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), index=True)
    content_hash: Mapped[str] = mapped_column(String(128))
    audit_reference: Mapped[str] = mapped_column(String(120))
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
