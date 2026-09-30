"""Task-aware model routing for the sovereign local model stack."""

from __future__ import annotations

from typing import Optional

from app.services.model_registry import ModelCapability, ModelSelection, ModelRegistry, model_registry
from app.services.query_router import query_router


class ModelRouter:
    """Select a model by task intent and capability, with safe fallback behavior."""

    def __init__(self, registry: Optional[ModelRegistry] = None) -> None:
        self.registry = registry or model_registry

    @staticmethod
    def _intent_to_capability(intent: Optional[str]) -> ModelCapability:
        normalized = (intent or "").strip().lower()
        intent_map = {
            "drawing": ModelCapability.VISION,
            "asset_lookup": ModelCapability.DOCUMENT_ANALYSIS,
            "compare": ModelCapability.DOCUMENT_ANALYSIS,
            "maintenance": ModelCapability.DOCUMENT_ANALYSIS,
            "semantic": ModelCapability.CHAT,
            "unknown": ModelCapability.CHAT,
            "chat": ModelCapability.CHAT,
            "code": ModelCapability.CODING,
            "coding": ModelCapability.CODING,
            "vision": ModelCapability.VISION,
            "document_summary": ModelCapability.DOCUMENT_ANALYSIS,
            "document_qa": ModelCapability.DOCUMENT_ANALYSIS,
        }
        return intent_map.get(normalized, ModelCapability.CHAT)

    def route_query(self, query: str, override: Optional[str] = None) -> ModelSelection:
        route = query_router.route(query or "")
        intent = route.get("intent") or "unknown"
        classified_task = self.registry.classify_task(query or "")
        task_type = intent if intent in {"drawing", "maintenance", "asset_lookup", "compare"} else classified_task
        visual_request = any(
            marker in (query or "").lower()
            for marker in ("analyze image", "inspect image", "what is shown", "visual analysis", "describe the drawing")
        )
        if task_type == "drawing" and not visual_request:
            task_type = "semantic"

        if override:
            forced = self.registry.resolve_override(override)
            if forced is not None:
                return ModelSelection(
                    task_type=task_type,
                    model_id=forced.id,
                    ollama_tag=forced.ollama_tag,
                    display_name=forced.display_name,
                    auto_selected=False,
                    reason=f"Manual override → {forced.ollama_tag}",
                )
        preferred_capability = self._intent_to_capability(task_type)

        candidates = self.registry.find_by_capability(preferred_capability)
        fallback_model = self.registry.enabled_chat_model()

        if candidates:
            selected = candidates[0]
            if selected.enabled:
                return ModelSelection(
                    task_type=task_type,
                    model_id=selected.id,
                    ollama_tag=selected.ollama_tag,
                    display_name=selected.display_name,
                    auto_selected=True,
                    reason=(
                        f"Intent '{task_type}' matched capability '{preferred_capability.value}' "
                        f"→ {selected.ollama_tag}"
                    ),
                )

        return ModelSelection(
            task_type=task_type,
            model_id=fallback_model.id,
            ollama_tag=fallback_model.ollama_tag,
            display_name=fallback_model.display_name,
            auto_selected=True,
            reason=(
                f"No enabled model for task '{task_type}' and capability '{preferred_capability.value}'; "
                f"falling back to {fallback_model.ollama_tag}"
            ),
        )


model_router = ModelRouter()

__all__ = ["ModelRouter", "model_router"]
