import hashlib
import hmac
import json
import os
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.auth import ROLE_CLEARANCE_MAP
from app.db.models import (
    AgentRunRecord,
    ArtifactRecord,
    AuditRecord,
    Base,
    ConversationRecord,
    MessageRecord,
    UserRecord,
)
from app.db.session import engine


def ensure_schema() -> None:
    # Production schema changes are applied by Alembic before the app starts.
    # Keep metadata creation only for isolated SQLite test databases.
    if engine.url.get_backend_name() == "sqlite":
        Base.metadata.create_all(bind=engine)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or os.urandom(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        _, salt_hex, digest_hex = encoded.split("$", 2)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.scrypt(
            password.encode(), salt=bytes.fromhex(salt_hex), n=16384, r=8, p=1
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def find_user(db: Session, username: str) -> UserRecord | None:
    return db.scalar(
        select(UserRecord).where(
            UserRecord.username == username.lower(), UserRecord.is_active.is_(True)
        )
    )


def bootstrap_users(db: Session) -> None:
    raw = os.getenv("AEGIS_BOOTSTRAP_USERS_JSON", "")
    if not raw:
        return
    for item in json.loads(raw):
        username = str(item["username"]).lower()
        role = str(item["role"]).upper()
        if role not in ROLE_CLEARANCE_MAP:
            raise ValueError(f"Unsupported bootstrap role: {role}")
        record = find_user(db, username)
        if record is None:
            record = UserRecord(username=username)
            db.add(record)
        record.password_hash = _hash_password(str(item["password"]))
        record.role = role
        record.clearance_tags = ROLE_CLEARANCE_MAP[role]
        record.is_active = True
    db.commit()


def serialize_run(record: AgentRunRecord) -> dict[str, Any]:
    return {
        "run_id": record.run_id,
        "user_id": str(record.user_id),
        "task": record.task,
        "model_id": record.model_id,
        "status": record.status,
        "steps": record.steps or [],
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "final_result": record.final_result,
        "error": record.error,
    }


def save_run(db: Session, data: dict[str, Any], user: UserRecord) -> dict[str, Any]:
    record = db.scalar(select(AgentRunRecord).where(AgentRunRecord.run_id == data["run_id"]))
    if record is None:
        record = AgentRunRecord(run_id=data["run_id"], user_id=user.id, username=user.username)
        db.add(record)
    record.user_id = user.id
    record.username = user.username
    record.task = data["task"]
    record.model_id = data.get("model_id") or "auto"
    record.status = data["status"]
    record.steps = data.get("steps") or []
    record.final_result = data.get("final_result")
    record.error = data.get("error")
    record.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(record)
    return serialize_run(record)


def list_runs(db: Session, user: UserRecord, include_all: bool = False) -> list[dict[str, Any]]:
    query = select(AgentRunRecord).order_by(AgentRunRecord.created_at.desc())
    if not include_all:
        query = query.where(AgentRunRecord.user_id == user.id)
    return [serialize_run(item) for item in db.scalars(query).all()]


def _conversation_owner_query(conversation_id: str, username: str, include_all: bool = False):
    query = select(ConversationRecord).where(ConversationRecord.conversation_id == conversation_id)
    if not include_all:
        query = query.where(ConversationRecord.owner_username == username.lower())
    return query


def serialize_message(record: MessageRecord) -> dict[str, Any]:
    return {
        "message_id": record.message_id,
        "conversation_id": record.conversation_id,
        "role": record.role,
        "content": record.content,
        "sequence": record.sequence,
        "status": record.status,
        "agent_run_id": record.agent_run_id,
        "metadata": record.metadata_json or {},
        "created_at": record.created_at.isoformat(),
    }


def serialize_conversation(
    record: ConversationRecord,
    messages: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = {
        "conversation_id": record.conversation_id,
        "owner": record.owner_username,
        "title": record.title,
        "classification": record.classification,
        "status": record.status,
        "created_at": record.created_at.isoformat(),
        "updated_at": record.updated_at.isoformat(),
        "last_message_at": record.last_message_at.isoformat() if record.last_message_at else None,
    }
    if messages is not None:
        result["messages"] = messages
    return result


def create_conversation(
    db: Session,
    username: str,
    user_id: int | None,
    classification: str = "INTERNAL",
    title: str = "New conversation",
) -> dict[str, Any]:
    import uuid

    now = datetime.now(timezone.utc)
    record = ConversationRecord(
        conversation_id=f"conv-{uuid.uuid4().hex}",
        owner_username=username.lower(),
        owner_user_id=user_id,
        title=title[:240] or "New conversation",
        classification=classification.upper(),
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_conversation(record)


def list_conversations(db: Session, username: str, include_all: bool = False) -> list[dict[str, Any]]:
    query = select(ConversationRecord).order_by(
        ConversationRecord.last_message_at.desc(),
        ConversationRecord.updated_at.desc(),
    )
    if not include_all:
        query = query.where(ConversationRecord.owner_username == username.lower())
    return [serialize_conversation(item) for item in db.scalars(query).all()]


def find_conversation(
    db: Session,
    conversation_id: str,
    username: str,
    include_all: bool = False,
) -> ConversationRecord | None:
    return db.scalar(_conversation_owner_query(conversation_id, username, include_all))


def append_message(
    db: Session,
    conversation: ConversationRecord,
    role: str,
    content: str,
    status: str = "COMPLETED",
    agent_run_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    latest = db.scalar(
        select(MessageRecord)
        .where(MessageRecord.conversation_id == conversation.conversation_id)
        .order_by(MessageRecord.sequence.desc())
    )
    now = datetime.now(timezone.utc)
    record = MessageRecord(
        message_id=f"msg-{__import__('uuid').uuid4().hex}",
        conversation_id=conversation.conversation_id,
        role=role.upper(),
        content=content,
        sequence=(latest.sequence + 1) if latest else 1,
        status=status,
        agent_run_id=agent_run_id,
        metadata_json=metadata or {},
        created_at=now,
    )
    conversation.updated_at = now
    conversation.last_message_at = now
    db.add(record)
    db.commit()
    db.refresh(record)
    return serialize_message(record)


def update_conversation_title(db: Session, conversation: ConversationRecord, title: str) -> None:
    if conversation.title == "New conversation":
        conversation.title = title.strip()[:240] or conversation.title
        db.commit()


def list_messages(db: Session, conversation_id: str) -> list[dict[str, Any]]:
    records = db.scalars(
        select(MessageRecord)
        .where(MessageRecord.conversation_id == conversation_id)
        .order_by(MessageRecord.sequence, MessageRecord.created_at)
    ).all()
    return [serialize_message(item) for item in records]


def save_audit_record(
    db: Session,
    data: dict[str, Any],
    user_id: int | None = None,
) -> dict[str, Any]:
    record = AuditRecord(
        id=data["id"],
        timestamp=data["timestamp"],
        event_type=data["event_type"],
        username=data.get("username"),
        user_id=user_id,
        run_id=data.get("run_id"),
        clearance_tags=data.get("clearance_tags") or [],
        query_or_action=data.get("query_or_action") or "",
        diagnosis_summary=data.get("diagnosis_summary") or "",
        citations_count=int(data.get("citations_count") or 0),
        hitl_approval_required=bool(data.get("hitl_approval_required")),
        equipment_tag=data.get("equipment_tag") or "N/A",
        status=data.get("status") or "LOGGED",
        previous_hash=data["previous_hash"],
        entry_hash=data["entry_hash"],
        integrity_hash=data.get("integrity_hash"),
        metadata_json=data.get("metadata") or {},
    )
    db.add(record)
    db.commit()
    return data


def list_audit_records(db: Session) -> list[dict[str, Any]]:
    records = db.scalars(select(AuditRecord).order_by(AuditRecord.timestamp, AuditRecord.id)).all()
    return [
        {
            "id": item.id,
            "timestamp": item.timestamp,
            "event_type": item.event_type,
            "username": item.username,
            "run_id": item.run_id,
            "clearance_tags": item.clearance_tags or [],
            "query_or_action": item.query_or_action,
            "diagnosis_summary": item.diagnosis_summary,
            "citations_count": item.citations_count,
            "hitl_approval_required": item.hitl_approval_required,
            "equipment_tag": item.equipment_tag,
            "status": item.status,
            "previous_hash": item.previous_hash,
            "entry_hash": item.entry_hash,
            "integrity_hash": item.integrity_hash,
            "metadata": item.metadata_json or {},
        }
        for item in records
    ]


def clear_audit_records(db: Session) -> None:
    db.execute(delete(AuditRecord))
    db.commit()


def save_artifact(db: Session, data: dict[str, Any]) -> dict[str, Any]:
    record = ArtifactRecord(
        artifact_id=data["artifact_id"],
        report_type=data["report_type"],
        format=data["format"],
        storage_name=data["storage_name"],
        created_by=data["created_by"],
        agent_run_id=data.get("agent_run_id"),
        classification=data["classification"],
        source_count=data["source_count"],
        status=data["status"],
        content_hash=data["content_hash"],
        audit_reference=data["audit_reference"],
        metadata_json=data.get("metadata") or {},
    )
    db.add(record)
    db.commit()
    return serialize_artifact(record)


def serialize_artifact(record: ArtifactRecord) -> dict[str, Any]:
    return {
        "artifact_id": record.artifact_id,
        "report_type": record.report_type,
        "format": record.format,
        "storage_name": record.storage_name,
        "created_by": record.created_by,
        "created_at": record.created_at.isoformat(),
        "agent_run_id": record.agent_run_id,
        "classification": record.classification,
        "source_count": record.source_count,
        "status": record.status,
        "content_hash": record.content_hash,
        "audit_reference": record.audit_reference,
        "metadata": record.metadata_json or {},
    }


def find_artifact(db: Session, artifact_id: str) -> ArtifactRecord | None:
    return db.scalar(select(ArtifactRecord).where(ArtifactRecord.artifact_id == artifact_id))


def update_artifact_status(db: Session, artifact_id: str, status: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    record = find_artifact(db, artifact_id)
    if record is None:
        raise LookupError("Artifact not found.")
    record.status = status
    if metadata:
        record.metadata_json = {**(record.metadata_json or {}), **metadata}
    db.commit()
    db.refresh(record)
    return serialize_artifact(record)
