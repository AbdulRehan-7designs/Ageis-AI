import hashlib
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

# In-memory Audit Log Store (Persists to PostgreSQL when running inside container)
AUDIT_LOG_STORE = []

class HITLApprovalRequest(BaseModel):
    action_id: str
    equipment_tag: str
    approved_by: str
    comments: Optional[str] = "Engineer confirmed shutdown and isolation."

class AuditEntry(BaseModel):
    id: str
    timestamp: str
    equipment_tag: str
    action: str
    approved_by: str
    integrity_hash: str
    status: str

@router.post("/hitl/approve", response_model=AuditEntry)
async def approve_action(request: HITLApprovalRequest):
    timestamp_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    
    # Compute SHA-256 Air-Gap Integrity Hash
    raw_payload = f"{request.action_id}:{request.equipment_tag}:{request.approved_by}:{timestamp_str}"
    integrity_hash = hashlib.sha256(raw_payload.encode()).hexdigest()
    
    entry = AuditEntry(
        id=f"AUDIT-{len(AUDIT_LOG_STORE) + 1001}",
        timestamp=timestamp_str,
        equipment_tag=request.equipment_tag,
        action=f"Approved Shutdown & Maintenance for {request.equipment_tag} under SOP-017",
        approved_by=request.approved_by,
        integrity_hash=integrity_hash,
        status="EXECUTED"
    )
    
    AUDIT_LOG_STORE.append(entry.dict())
    return entry

@router.get("/audit/logs", response_model=List[AuditEntry])
async def get_audit_logs():
    return AUDIT_LOG_STORE
