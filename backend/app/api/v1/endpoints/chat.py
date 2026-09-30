"""Chat endpoint for the AegisAI sovereign chat workbench."""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.auth import User, get_current_user
from app.db.repository import append_message, create_conversation, find_conversation, list_messages, update_conversation_title
from app.db.session import SessionLocal
from app.services.agent_orchestrator import agent_orchestrator
from app.services.audit_service import audit_service
from app.services.report_service import report_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    model_override: Optional[str] = None
    conversation_id: Optional[str] = None


def _normalize_result(result: dict) -> dict:
    normalized_citations = []
    for item in result.get("citations", []):
        normalized = dict(item)
        normalized.setdefault("document", normalized.get("document_name") or normalized.get("document") or "Source Document")
        normalized.setdefault("document_name", normalized.get("document") or normalized.get("document_name") or "Source Document")
        normalized.setdefault("tag", normalized.get("classification_tag") or "INTERNAL")
        normalized.setdefault("classification_tag", normalized.get("tag") or "INTERNAL")
        normalized_citations.append(normalized)
    result["citations"] = normalized_citations
    return result


@router.post("/chat")
async def chat(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Route a user message through the Aegis AI orchestrator."""
    with SessionLocal() as db:
        conversation = _conversation_for_request(db, request.conversation_id, current_user)
        conversation_history = list_messages(db, conversation.conversation_id)
        append_message(db, conversation, "USER", request.message)
        update_conversation_title(db, conversation, request.message)
        conversation_id = conversation.conversation_id
    result = await agent_orchestrator.process_query(
        user_message=request.message,
        model_override=request.model_override,
        user_clearance=current_user.clearance_tags,
        username=current_user.username,
        conversation_history=conversation_history,
    )
    result = _normalize_result(result)
    _persist_assistant_message(conversation_id, current_user, result)
    result["conversation_id"] = conversation_id
    return result


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, current_user: User = Depends(get_current_user)):
    """Return an SSE-style chat stream for progressive UI rendering."""
    with SessionLocal() as db:
        conversation = _conversation_for_request(db, request.conversation_id, current_user)
        conversation_history = list_messages(db, conversation.conversation_id)
        append_message(db, conversation, "USER", request.message)
        update_conversation_title(db, conversation, request.message)
        conversation_id = conversation.conversation_id

    async def generate():
        yield f"data: {json.dumps({'type': 'status', 'content': 'Retrieving authorized evidence...'})}\n\n"
        result = await agent_orchestrator.process_query(
            user_message=request.message,
            model_override=request.model_override,
            user_clearance=current_user.clearance_tags,
            username=current_user.username,
            conversation_history=conversation_history,
        )
        result = _normalize_result(result)
        _persist_assistant_message(conversation_id, current_user, result)
        result["conversation_id"] = conversation_id
        message_text = str(result.get("diagnosis_summary") or result.get("reply_title") or "I analyzed the evidence and will return a traceable answer.")
        chunk_size = 24
        for idx in range(0, len(message_text), chunk_size):
            chunk = message_text[idx:idx + chunk_size]
            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'type': 'final', 'result': result})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _conversation_for_request(db, conversation_id: str | None, current_user: User):
    if not conversation_id:
        classification = (
            current_user.clearance_tags[0]
            if current_user.clearance_tags
            else "PUBLIC"
        )
        created = create_conversation(
            db,
            current_user.username,
            current_user.id,
            classification=classification,
        )
        return find_conversation(db, created["conversation_id"], current_user.username)
    conversation = find_conversation(db, conversation_id, current_user.username, include_all=current_user.role == "ADMIN")
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    if not report_service.classification_allowed(conversation.classification, current_user.clearance_tags):
        raise HTTPException(status_code=403, detail="Conversation classification exceeds the user's clearance.")
    return conversation


def _persist_assistant_message(conversation_id: str | None, current_user: User, result: dict) -> None:
    if not conversation_id:
        return
    agent_run = result.get("agent_run") or {}
    metadata = {
        "citations": result.get("citations") or [],
        "evidence_blocks": result.get("evidence_blocks") or [],
        "evidence_confidence": result.get("evidence_confidence"),
        "evidence_state": result.get("evidence_state"),
        "evidence_warnings": result.get("evidence_warnings") or [],
        "reply_title": result.get("reply_title"),
    }
    content = str(result.get("diagnosis_summary") or result.get("reply_title") or "I analyzed the evidence and will return a traceable answer.")
    with SessionLocal() as db:
        conversation = _conversation_for_request(db, conversation_id, current_user)
        append_message(
            db,
            conversation,
            "ASSISTANT",
            content,
            agent_run_id=agent_run.get("run_id"),
            metadata=metadata,
        )
    audit_service.log_entry(
        event_type="CONVERSATION_MESSAGE_CREATED",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action="Persist assistant conversation message",
        equipment_tag="N/A",
        citations_count=len(metadata["citations"]),
        status="CREATED",
        run_id=agent_run.get("run_id"),
        metadata={"conversation_id": conversation_id},
    )
