from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth import User, get_current_user
from app.db.repository import (
    append_message,
    create_conversation,
    find_conversation,
    list_conversations,
    list_messages,
)
from app.db.session import SessionLocal
from app.services.audit_service import audit_service
from app.services.report_service import report_service

router = APIRouter()


class ConversationCreateRequest(BaseModel):
    title: str = Field(default="New conversation", max_length=240)


def _authorized_conversation(db, conversation_id: str, current_user: User):
    record = find_conversation(
        db,
        conversation_id,
        current_user.username,
        include_all=current_user.role == "ADMIN",
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    if not report_service.classification_allowed(record.classification, current_user.clearance_tags):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Conversation classification exceeds the user's clearance.")
    return record


@router.post("/conversations")
async def create_user_conversation(
    request: ConversationCreateRequest,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        classification = current_user.clearance_tags[0] if current_user.clearance_tags else "PUBLIC"
        result = create_conversation(
            db,
            current_user.username,
            current_user.id,
            classification=classification,
            title=request.title,
        )
    audit_service.log_entry(
        event_type="CONVERSATION_CREATED",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action="Create conversation",
        equipment_tag="N/A",
        status="CREATED",
        metadata={"conversation_id": result["conversation_id"]},
    )
    return result


@router.get("/conversations")
async def get_user_conversations(current_user: User = Depends(get_current_user)):
    with SessionLocal() as db:
        records = list_conversations(db, current_user.username, include_all=current_user.role == "ADMIN")
        return [
            item for item in records
            if report_service.classification_allowed(item["classification"], current_user.clearance_tags)
        ]


@router.get("/conversations/{conversation_id}")
async def get_user_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        record = _authorized_conversation(db, conversation_id, current_user)
        result = {
            "conversation_id": record.conversation_id,
            "owner": record.owner_username,
            "title": record.title,
            "classification": record.classification,
            "status": record.status,
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat(),
            "last_message_at": record.last_message_at.isoformat() if record.last_message_at else None,
            "messages": list_messages(db, record.conversation_id),
        }
    return result


class MessageCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=100000)


@router.post("/conversations/{conversation_id}/messages")
async def add_conversation_message(
    conversation_id: str,
    request: MessageCreateRequest,
    current_user: User = Depends(get_current_user),
):
    with SessionLocal() as db:
        record = _authorized_conversation(db, conversation_id, current_user)
        message = append_message(db, record, "USER", request.content)
    audit_service.log_entry(
        event_type="CONVERSATION_MESSAGE_CREATED",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action="Persist user conversation message",
        equipment_tag="N/A",
        status="CREATED",
        metadata={"conversation_id": conversation_id, "message_id": message["message_id"]},
    )
    return message
