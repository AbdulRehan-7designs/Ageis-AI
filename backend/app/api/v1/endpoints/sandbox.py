from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import User, require_role, get_current_user
from app.core.config import settings
from app.services.sandbox import sandbox_service, SandboxExecutionRequest, SandboxExecutionResult
from app.services.audit_service import audit_service

router = APIRouter()


@router.post("/sandbox/execute", response_model=SandboxExecutionResult)
async def execute_sandboxed_script(
    request: SandboxExecutionRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute diagnostic code in the isolated sovereign sandbox."""
    result = sandbox_service.execute(
        code=request.code,
        timeout_sec=request.timeout_sec,
        inputs=request.inputs or request.context_vars,
        purpose=request.purpose,
    )
    audit_service.log_entry(
        event_type="SANDBOX_EXECUTION",
        username=current_user.username,
        clearance_tags=current_user.clearance_tags,
        query_or_action="python_sandbox",
        diagnosis_summary=f"Sandbox execution {result.status.lower()}",
        citations_count=0,
        hitl_approval_required=False,
        equipment_tag="N/A",
        status=result.status,
        metadata={
            "sandbox_id": result.sandbox_id,
            "tool_name": "python_sandbox",
            "code_hash": result.code_hash,
            "execution_time_ms": result.execution_time_ms,
            "resource_limits": {
                "timeout_seconds": request.timeout_sec,
                "memory_mb": settings.SANDBOX_MEMORY_MB,
                "max_output_bytes": settings.SANDBOX_MAX_OUTPUT_BYTES,
            },
        },
    )
    return result
