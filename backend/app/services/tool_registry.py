"""Controlled, allow-listed tool registry for AegisAI agent execution."""

from __future__ import annotations

import ast
import math
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from app.core.config import settings
from app.services.rag_service import rag_service
from app.services.sandbox import sandbox_service

_ALLOWED_DOCUMENT_ROOT = (Path(__file__).resolve().parent.parent / "uploaded_docs").resolve()


class ToolRiskLevel(str, Enum):
    READ_ONLY = "READ_ONLY"
    LOW_RISK = "LOW_RISK"
    REQUIRES_APPROVAL = "REQUIRES_APPROVAL"
    RESTRICTED = "RESTRICTED"


class ToolDefinition(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    risk_level: ToolRiskLevel = ToolRiskLevel.READ_ONLY
    enabled: bool = True
    requires_approval: bool = False
    handler: Optional[Callable[..., Dict[str, Any]]] = Field(default=None, exclude=True)

    def validate_arguments(self, arguments: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if arguments is None:
            arguments = {}
        if not isinstance(arguments, dict):
            raise ValueError(f"Tool '{self.name}' requires a dictionary of arguments.")

        required = set(self.input_schema.get("required", []))
        for field_name in sorted(required):
            if field_name not in arguments or arguments[field_name] in (None, ""):
                raise ValueError(f"Tool '{self.name}' is missing required argument '{field_name}'.")

        properties = self.input_schema.get("properties", {})
        for key, value in arguments.items():
            metadata = properties.get(key, {})
            expected_type = metadata.get("type")
            if expected_type == "string" and value is not None and not isinstance(value, str):
                raise ValueError(f"Tool '{self.name}' argument '{key}' must be a string.")
            if expected_type == "integer" and value is not None and not isinstance(value, int):
                raise ValueError(f"Tool '{self.name}' argument '{key}' must be an integer.")
            if expected_type == "number" and value is not None and not isinstance(value, (int, float)):
                raise ValueError(f"Tool '{self.name}' argument '{key}' must be numeric.")
        return dict(arguments)


class ToolRegistry:
    """Allow-listed registry for agent execution tools."""

    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_core_tools()

    def _register_core_tools(self) -> None:
        self.register(
            ToolDefinition(
                name="document_search",
                description="Search the authorized knowledge base for evidence and citations.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer"},
                        "classification": {"type": "string"},
                    },
                    "required": ["query"],
                },
                output_schema={"type": "object"},
                risk_level=ToolRiskLevel.READ_ONLY,
                enabled=True,
                requires_approval=False,
                handler=self._document_search_handler,
            )
        )
        self.register(
            ToolDefinition(
                name="document_read",
                description="Read a document from the approved upload directory only.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "stored_filename": {"type": "string"},
                        "doc_name": {"type": "string"},
                        "max_chars": {"type": "integer"},
                    },
                    "required": [],
                },
                output_schema={"type": "object"},
                risk_level=ToolRiskLevel.READ_ONLY,
                enabled=True,
                requires_approval=False,
                handler=self._document_read_handler,
            )
        )
        self.register(
            ToolDefinition(
                name="calculator",
                description="Safely evaluate a constrained arithmetic expression for industrial calculations.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string"},
                    },
                    "required": ["expression"],
                },
                output_schema={"type": "object"},
                risk_level=ToolRiskLevel.LOW_RISK,
                enabled=True,
                requires_approval=False,
                handler=self._calculator_handler,
            )
        )
        self.register(
            ToolDefinition(
                name="python_sandbox",
                description="Run bounded Python calculations in the isolated execution sandbox.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "code": {"type": "string"},
                        "inputs": {"type": "object"},
                        "purpose": {"type": "string"},
                    },
                    "required": ["code"],
                },
                output_schema={"type": "object"},
                risk_level=ToolRiskLevel.LOW_RISK,
                handler=self._python_sandbox_handler,
            )
        )

    def register(self, tool: ToolDefinition) -> ToolDefinition:
        if not tool.name:
            raise ValueError("Tool name is required.")
        if tool.name in self._tools and self._tools[tool.name].enabled:
            raise ValueError(f"Tool '{tool.name}' is already registered.")
        self._tools[tool.name] = tool
        return tool

    def get(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, include_disabled: bool = False) -> List[ToolDefinition]:
        tools = list(self._tools.values())
        if not include_disabled:
            tools = [tool for tool in tools if tool.enabled]
        return tools

    def validate(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> ToolDefinition:
        tool = self.get(name)
        if tool is None:
            raise KeyError(f"Unknown tool '{name}'.")
        if not tool.enabled:
            raise ValueError(f"Tool '{name}' is disabled.")
        tool.validate_arguments(arguments)
        return tool

    def execute(self, name: str, arguments: Optional[Dict[str, Any]] = None, **context: Any) -> Dict[str, Any]:
        tool = self.validate(name, arguments)
        if tool.handler is None:
            raise ValueError(f"Tool '{name}' has no callable handler.")
        safe_arguments = tool.validate_arguments(arguments)
        return tool.handler(safe_arguments, **context)

    @staticmethod
    def _document_search_handler(arguments: Dict[str, Any], **context: Any) -> Dict[str, Any]:
        query = str(arguments.get("query") or "").strip()
        if not query:
            raise ValueError("document_search requires a non-empty query.")
        clearance = context.get("user_clearance") or [settings.CLASSIFICATION_TAG_DEFAULT]
        top_k = int(arguments.get("top_k") or 5)
        classification = arguments.get("classification")

        rag_context = rag_service.build_rag_context(
            query=query,
            user_clearance=list(clearance),
            top_k=max(1, min(top_k, 10)),
        )

        hits: List[Dict[str, Any]] = []
        for citation in rag_context.get("citations", []) or []:
            if classification and str(citation.get("tag") or citation.get("classification_tag") or "").upper() != str(classification).upper():
                continue
            hits.append(
                {
                    "document": citation.get("document_name") or citation.get("document") or "Source Document",
                    "page": citation.get("page") or 1,
                    "section": citation.get("section_title") or citation.get("section") or "N/A",
                    "classification": citation.get("tag") or citation.get("classification_tag") or settings.CLASSIFICATION_TAG_DEFAULT,
                    "content": citation.get("snippet") or citation.get("text") or "",
                    "score": citation.get("score") or 0.0,
                    "chunk_id": citation.get("chunk_id"),
                    "source": citation.get("source") or citation.get("document_name") or citation.get("document") or "knowledge-base",
                }
            )

        return {
            "query": query,
            "results": hits,
            "count": len(hits),
            "route": rag_context.get("query_route"),
            "result_count": rag_context.get("result_count", len(hits)),
        }

    @staticmethod
    def _document_read_handler(arguments: Dict[str, Any], **context: Any) -> Dict[str, Any]:
        stored_filename = arguments.get("stored_filename")
        doc_name = arguments.get("doc_name")
        max_chars = int(arguments.get("max_chars") or 4000)

        candidate = stored_filename or doc_name
        if not candidate:
            raise ValueError("document_read requires a stored_filename or doc_name.")

        base_dir = _ALLOWED_DOCUMENT_ROOT.resolve()
        base_dir.mkdir(exist_ok=True)

        requested = Path(candidate)
        if requested.is_absolute() or ".." in requested.parts or candidate.startswith("../") or candidate.startswith("..\\") or candidate.startswith("/"):
            raise ValueError("Path traversal is not allowed in document_read.")

        safe_target = (base_dir / requested.name).resolve()
        try:
            safe_target.relative_to(base_dir)
        except ValueError as exc:
            raise ValueError("Path traversal is not allowed in document_read.") from exc

        if not safe_target.exists() or not safe_target.is_file():
            raise FileNotFoundError(f"Document '{candidate}' was not found in the approved document store.")

        if safe_target.suffix.lower() not in {".txt", ".md", ".json", ".csv", ".pdf"}:
            raise ValueError("document_read only allows approved document file types.")

        if safe_target.suffix.lower() == ".pdf":
            return {
                "document": safe_target.name,
                "path": str(safe_target),
                "kind": "pdf",
                "bytes": safe_target.stat().st_size,
                "content_preview": "[PDF document preview unavailable in the secure tool layer]",
                "max_chars": max_chars,
            }

        text = safe_target.read_text(encoding="utf-8", errors="replace")
        preview = text[:max_chars]
        return {
            "document": safe_target.name,
            "path": str(safe_target),
            "kind": safe_target.suffix.lower().lstrip("."),
            "bytes": safe_target.stat().st_size,
            "content_preview": preview,
            "max_chars": max_chars,
        }

    @staticmethod
    def _calculator_handler(arguments: Dict[str, Any], **context: Any) -> Dict[str, Any]:
        expression = str(arguments.get("expression") or "").strip()
        if not expression:
            raise ValueError("calculator requires a non-empty expression.")

        safe_allowed = {
            ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd,
            ast.Mod, ast.FloorDiv, ast.Call, ast.Attribute, ast.Load, ast.Name,
            ast.Tuple, ast.List, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Expression,
        }

        try:
            parsed = ast.parse(expression, mode="eval")
        except SyntaxError as exc:
            raise ValueError(f"Invalid arithmetic expression: {exc.msg}") from exc

        for node in ast.walk(parsed):
            if type(node) not in safe_allowed:
                raise ValueError(f"Unsupported operation in calculator expression: {type(node).__name__}")
            if isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name not in {"sqrt", "sin", "cos", "tan", "log", "exp", "pow"}:
                    raise ValueError(f"Unsupported function in calculator expression: {func_name or 'unknown'}")
            if isinstance(node, ast.Name) and node.id not in {"pi", "e"}:
                raise ValueError(f"Unsupported variable in calculator expression: {node.id}")

        allowed_names = {"math": math, "pi": math.pi, "e": math.e, "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan, "log": math.log, "exp": math.exp, "pow": pow}

        def _safe_eval(node: ast.AST) -> Any:
            if isinstance(node, ast.Expression):
                return _safe_eval(node.body)
            if isinstance(node, ast.Constant):
                return node.value
            if isinstance(node, ast.BinOp):
                left = _safe_eval(node.left)
                right = _safe_eval(node.right)
                if isinstance(node.op, ast.Add):
                    return left + right
                if isinstance(node.op, ast.Sub):
                    return left - right
                if isinstance(node.op, ast.Mult):
                    return left * right
                if isinstance(node.op, ast.Div):
                    return left / right
                if isinstance(node.op, ast.FloorDiv):
                    return left // right
                if isinstance(node.op, ast.Mod):
                    return left % right
                if isinstance(node.op, ast.Pow):
                    return left ** right
                raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")
            if isinstance(node, ast.UnaryOp):
                operand = _safe_eval(node.operand)
                if isinstance(node.op, ast.UAdd):
                    return +operand
                if isinstance(node.op, ast.USub):
                    return -operand
                raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")
            if isinstance(node, ast.Call):
                func = node.func
                if isinstance(func, ast.Name):
                    name = func.id
                    if name not in allowed_names:
                        raise ValueError(f"Unsupported function call: {name}")
                    args = [_safe_eval(arg) for arg in node.args]
                    return allowed_names[name](*args)
                raise ValueError("Only direct function calls are supported in the calculator.")
            if isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                raise ValueError(f"Unsupported symbol: {node.id}")
            raise ValueError(f"Unsupported expression node: {type(node).__name__}")

        result = _safe_eval(parsed)
        return {
            "expression": expression,
            "result": result,
            "method": "safe_calculator",
        }

    @staticmethod
    def _python_sandbox_handler(arguments: Dict[str, Any], **context: Any) -> Dict[str, Any]:
        result = sandbox_service.execute(
            code=str(arguments.get("code") or ""),
            inputs=arguments.get("inputs") or {},
            purpose=str(arguments.get("purpose") or "engineering_calculation"),
        )
        return result.model_dump()


tool_registry = ToolRegistry()

__all__ = ["ToolDefinition", "ToolRegistry", "ToolRiskLevel", "tool_registry"]
