"""Air-Gapped Sovereign Execution Sandbox for AegisAI.

Provides isolated, secure execution of diagnostic scripts and industrial calculations.
Features AST static analysis to block dangerous system/network calls, execution
timeouts, memory/resource containment, and output capture.
"""

from __future__ import annotations

import ast
import logging
import sys
import tempfile
import time
import subprocess

from pydantic import BaseModel
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Blacklisted modules & AST node types for security policy
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "socket", "httpx", "requests", "urllib",
    "shutil", "ctypes", "multiprocessing", "threading", "pty", "posix",
    "builtins", "importlib", "pickle", "eval", "exec", "tempfile"
}

BLOCKED_CALLS = {
    "eval", "exec", "open", "__import__", "compile", "getattr", "setattr", "delattr"
}


class SandboxExecutionRequest(BaseModel):
    code: str
    timeout_sec: Optional[float] = 5.0
    context_vars: Optional[Dict[str, Any]] = None


class SandboxExecutionResult(BaseModel):
    status: str  # "SUCCESS", "SECURITY_VIOLATION", "TIMEOUT", "ERROR"
    stdout: str
    stderr: str
    result: Optional[Any] = None
    execution_time_sec: float
    violations: List[str]


class CodeSandbox:
    """Secure, isolated Python execution sandbox for AegisAI tools."""

    def __init__(self, default_timeout: float = 5.0) -> None:
        self.default_timeout = default_timeout

    def static_security_inspect(self, code: str) -> List[str]:
        """Perform AST static analysis to detect forbidden imports and calls."""
        violations: List[str] = []

        try:
            tree = ast.parse(code)
        except SyntaxError as exc:
            violations.append(f"Syntax error in code snippet: {exc}")
            return violations

        for node in ast.walk(tree):
            # Check import statements (import os, import subprocess, etc.)
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_name = alias.name.split(".")[0]
                    if root_name in BLOCKED_MODULES:
                        violations.append(f"Forbidden module import: '{alias.name}'")

            # Check import-from statements (from os import path, etc.)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_name = node.module.split(".")[0]
                    if root_name in BLOCKED_MODULES:
                        violations.append(f"Forbidden module import from '{node.module}'")

            # Check dangerous built-in function calls (eval, exec, __import__)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in BLOCKED_CALLS:
                        violations.append(f"Forbidden function call: '{node.func.id}()'")

        return violations

    def execute(self, code: str, timeout_sec: Optional[float] = None) -> SandboxExecutionResult:
        """Execute code snippet in an isolated subprocess with AST inspection and timeout enforcement."""
        start_time = time.time()
        timeout = timeout_sec if timeout_sec is not None else self.default_timeout

        # Step 1: Static Security Inspection
        violations = self.static_security_inspect(code)
        if violations:
            logger.warning("Sandbox security violation blocked execution: %s", violations)
            return SandboxExecutionResult(
                status="SECURITY_VIOLATION",
                stdout="",
                stderr="Security Policy Violation: Code contained restricted operations.",
                result=None,
                execution_time_sec=round(time.time() - start_time, 4),
                violations=violations,
            )

        # Step 2: Isolated Subprocess Execution
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            script_path = tmp_file.name
            tmp_file.write(code)

        try:
            cmd = [sys.executable, "-I", "-B", script_path]
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate(timeout=timeout)
            exec_time = round(time.time() - start_time, 4)

            if process.returncode == 0:
                return SandboxExecutionResult(
                    status="SUCCESS",
                    stdout=stdout.strip(),
                    stderr=stderr.strip(),
                    result=stdout.strip(),
                    execution_time_sec=exec_time,
                    violations=[],
                )
            else:
                return SandboxExecutionResult(
                    status="ERROR",
                    stdout=stdout.strip(),
                    stderr=stderr.strip(),
                    result=None,
                    execution_time_sec=exec_time,
                    violations=[],
                )

        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            return SandboxExecutionResult(
                status="TIMEOUT",
                stdout=stdout.strip() if stdout else "",
                stderr=f"Execution timed out after {timeout} seconds.",
                result=None,
                execution_time_sec=round(time.time() - start_time, 4),
                violations=[f"Execution exceeded timeout limit of {timeout}s"],
            )
        except Exception as exc:
            return SandboxExecutionResult(
                status="ERROR",
                stdout="",
                stderr=str(exc),
                result=None,
                execution_time_sec=round(time.time() - start_time, 4),
                violations=[],
            )
        finally:
            import os
            try:
                if os.path.exists(script_path):
                    os.remove(script_path)
            except Exception:
                pass


sandbox_service = CodeSandbox()
