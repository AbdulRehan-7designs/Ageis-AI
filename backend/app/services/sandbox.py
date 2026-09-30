"""Controlled Python sandbox client with a development-only compatibility fallback."""

from __future__ import annotations

import ast
import hashlib
import json
import logging
import os
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)

BLOCKED_MODULES = {
    "os", "sys", "subprocess", "socket", "httpx", "requests", "urllib",
    "shutil", "ctypes", "multiprocessing", "threading", "pty", "posix",
    "builtins", "importlib", "pickle", "eval", "exec", "tempfile",
}
BLOCKED_CALLS = {"eval", "exec", "open", "__import__", "compile", "getattr", "setattr", "delattr"}


class SandboxExecutionRequest(BaseModel):
    code: str = Field(min_length=1, max_length=32768)
    timeout_sec: Optional[float] = Field(default=None, gt=0, le=30)
    context_vars: Optional[Dict[str, Any]] = None
    inputs: Optional[Dict[str, Any]] = None
    purpose: str = Field(default="engineering_calculation", max_length=120)


class SandboxExecutionResult(BaseModel):
    status: str
    stdout: str = ""
    stderr: str = ""
    result: Optional[Any] = None
    execution_time_sec: float = 0.0
    execution_time_ms: int = 0
    violations: List[str] = []
    sandbox_id: str = ""
    network_enabled: bool = False
    code_hash: str = ""


class CodeSandbox:
    def __init__(self, default_timeout: float = 5.0) -> None:
        self.default_timeout = default_timeout

    def static_security_inspect(self, code: str) -> List[str]:
        violations: List[str] = []
        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            return [f"Syntax error in code snippet: {exc}"]
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = node.names if isinstance(node, ast.Import) else [ast.alias(name=node.module or "")]
                for alias in names:
                    if alias.name.split(".")[0] in BLOCKED_MODULES:
                        violations.append(f"Forbidden module import: '{alias.name}'")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
                violations.append(f"Forbidden function call: '{node.func.id}()'")
        return violations

    def execute(
        self,
        code: str,
        timeout_sec: Optional[float] = None,
        inputs: Optional[Dict[str, Any]] = None,
        purpose: str = "engineering_calculation",
    ) -> SandboxExecutionResult:
        started = time.monotonic()
        code_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
        sandbox_id = hashlib.sha256(f"{code_hash}:{started}".encode()).hexdigest()[:20]
        if len(code.encode("utf-8")) > settings.SANDBOX_MAX_INPUT_BYTES:
            return self._result("INPUT_REJECTED", sandbox_id, code_hash, started, violations=["Input exceeds sandbox limit."])
        violations = self.static_security_inspect(code)
        if violations:
            return self._result("SECURITY_VIOLATION", sandbox_id, code_hash, started, stderr="Security policy violation.", violations=violations)

        request = {
            "code": code,
            "inputs": inputs or {},
            "purpose": purpose,
            "timeout_sec": timeout_sec or settings.SANDBOX_TIMEOUT_SECONDS,
            "sandbox_id": sandbox_id,
        }
        if settings.SANDBOX_URL:
            try:
                response = httpx.post(
                    f"{settings.SANDBOX_URL.rstrip('/')}/execute",
                    json=request,
                    timeout=(2.0, float(request["timeout_sec"]) + 3.0),
                )
                response.raise_for_status()
                return SandboxExecutionResult.model_validate(response.json())
            except Exception as exc:
                if not settings.SANDBOX_ALLOW_LOCAL_FALLBACK:
                    return self._result("SANDBOX_UNAVAILABLE", sandbox_id, code_hash, started, stderr="Isolated sandbox unavailable.")
                logger.warning("Isolated sandbox unavailable; using development compatibility fallback: %s", exc)
        return self._local_compatibility_execute(code, request, sandbox_id, code_hash, started)

    def _local_compatibility_execute(self, code: str, request: Dict[str, Any], sandbox_id: str, code_hash: str, started: float) -> SandboxExecutionResult:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp:
            script_path = tmp.name
            tmp.write(code)
        try:
            process = subprocess.Popen(
                [sys.executable, "-I", "-B", script_path],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                env={"PYTHONNOUSERSITE": "1"},
            )
            try:
                stdout, stderr = process.communicate(timeout=float(request["timeout_sec"]))
            except subprocess.TimeoutExpired:
                process.kill()
                stdout, stderr = process.communicate()
                return self._result("TIMEOUT", sandbox_id, code_hash, started, stdout, f"Execution timed out after {request['timeout_sec']} seconds.", [f"Execution exceeded timeout limit of {request['timeout_sec']}s"])
            stdout = stdout[: settings.SANDBOX_MAX_OUTPUT_BYTES].strip()
            stderr = stderr[: settings.SANDBOX_MAX_OUTPUT_BYTES].strip()
            status = "SUCCESS" if process.returncode == 0 else "ERROR"
            return self._result(status, sandbox_id, code_hash, started, stdout, stderr, result=stdout.strip())
        finally:
            try:
                os.remove(script_path)
            except OSError:
                pass

    @staticmethod
    def _result(status: str, sandbox_id: str, code_hash: str, started: float, stdout: str = "", stderr: str = "", result: Any = None, violations: Optional[List[str]] = None) -> SandboxExecutionResult:
        elapsed = round(time.monotonic() - started, 4)
        return SandboxExecutionResult(
            status=status, stdout=stdout, stderr=stderr, result=result,
            execution_time_sec=elapsed, execution_time_ms=int(elapsed * 1000),
            violations=violations or [], sandbox_id=sandbox_id,
            network_enabled=False, code_hash=code_hash,
        )


sandbox_service = CodeSandbox()
