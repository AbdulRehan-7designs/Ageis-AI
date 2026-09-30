from typing import Any, Dict, List

from fastapi import APIRouter

from app.services.model_registry import AUTO_SELECT_ID, model_registry

router = APIRouter()


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """Catalog of local open-weight models the workbench can route to."""
    models: List[Dict[str, Any]] = [
        {
            "id": AUTO_SELECT_ID,
            "ollama_tag": None,
            "display_name": "Auto (task router)",
            "task_types": ["chat", "document_summary", "code"],
            "description": "Pick chat vs coder from the query. Required SIH demo path.",
            "vram_hint": "varies",
            "enabled": True,
            "auto": True,
        }
    ]
    for model in model_registry.list_models(include_disabled=True):
        models.append(
            {
                "id": model.id,
                "ollama_tag": model.ollama_tag,
                "display_name": model.display_name,
                "task_types": model.task_types,
                "description": model.description,
                "vram_hint": model.vram_hint,
                "enabled": model.enabled,
                "auto": False,
            }
        )
    return {"default_id": AUTO_SELECT_ID, "models": models}
