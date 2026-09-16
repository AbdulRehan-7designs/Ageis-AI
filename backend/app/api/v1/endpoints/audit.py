import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.services.audit_service import audit_service

router = APIRouter()


class HITLApprovalRequest(BaseModel):
    action_id: str
    equipment_tag: str
    approved_by: str
    comments: Optional[str] = "Engineer confirmed shutdown and isolation."


class AuditEntry(BaseModel):
    id: str
    timestamp: str
    event_type: Optional[str] = "HITL_APPROVAL"
    username: Optional[str] = "sovereign_operator"
    clearance_tags: Optional[List[str]] = ["INTERNAL"]
    query_or_action: Optional[str] = ""
    diagnosis_summary: Optional[str] = ""
    citations_count: Optional[int] = 0
    hitl_approval_required: Optional[bool] = False
    equipment_tag: str
    action: Optional[str] = ""
    approved_by: Optional[str] = ""
    integrity_hash: Optional[str] = ""
    previous_hash: Optional[str] = ""
    entry_hash: Optional[str] = ""
    status: str


class ChainVerificationResponse(BaseModel):
    is_valid: bool
    total_entries: int
    broken_index: Optional[int] = None
    broken_entry_id: Optional[str] = None
    reason: Optional[str] = None


@router.post("/hitl/approve", response_model=AuditEntry)
async def approve_action(request: HITLApprovalRequest):
    entry_dict = audit_service.log_entry(
        event_type="HITL_APPROVAL",
        username=request.approved_by,
        clearance_tags=["RESTRICTED", "INTERNAL", "PUBLIC"],
        query_or_action=f"Approved Shutdown & Maintenance for {request.equipment_tag} under SOP-017",
        equipment_tag=request.equipment_tag,
        status="EXECUTED",
    )
    # Create copy for response without mutating stored entry in audit_service._store
    response_data = dict(entry_dict)
    response_data["action"] = entry_dict["query_or_action"]
    response_data["approved_by"] = request.approved_by
    return AuditEntry(**response_data)


@router.get("/audit/logs", response_model=List[Dict[str, Any]])
async def get_audit_logs():
    return audit_service.get_logs()


@router.get("/audit/verify", response_model=ChainVerificationResponse)
async def verify_audit_logs():
    return audit_service.verify_audit_chain()
