from fastapi import APIRouter, Depends, HTTPException
from app.core.auth import User, require_role, get_current_user
from app.services.sandbox import sandbox_service, SandboxExecutionRequest, SandboxExecutionResult

router = APIRouter()


@router.post("/sandbox/execute", response_model=SandboxExecutionResult)
async def execute_sandboxed_script(
    request: SandboxExecutionRequest,
    current_user: User = Depends(get_current_user),
):
    """Execute diagnostic code in the isolated sovereign sandbox."""
    result = sandbox_service.execute(code=request.code, timeout_sec=request.timeout_sec)
    return result
