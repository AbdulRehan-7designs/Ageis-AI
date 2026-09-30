"""Protected local visual analysis for authorized indexed documents."""

from __future__ import annotations

import base64
import json
import os
import re
import uuid
from typing import Any, Dict, List, Optional

import pymupdf as fitz

from app.core.config import settings
from app.core.auth import User
from app.services.audit_service import audit_service
from app.services.identifiers import extract_identifiers
from app.services.ingestion import IngestionService, ingestion_service
from app.services.model_registry import ModelProviderError, ModelRegistry, model_registry


class VisionAnalysisError(RuntimeError):
    """Controlled failure raised by protected visual analysis."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


class VisionAnalysisService:
    """Resolve authorized local documents and invoke the configured local vision model."""

    ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}

    def __init__(
        self,
        ingestion: Optional[IngestionService] = None,
        registry: Optional[ModelRegistry] = None,
    ) -> None:
        self.ingestion = ingestion or ingestion_service
        self.registry = registry or model_registry

    def _find_document(self, document_id: str, user: User) -> Dict[str, Any]:
        if not document_id or "/" in document_id or "\\" in document_id:
            raise VisionAnalysisError("A valid document identifier is required.", 400)
        allowed = {tag.upper() for tag in user.clearance_tags}
        offset = None
        try:
            while True:
                points, offset = self.ingestion.qdrant_client.scroll(
                    collection_name=self.ingestion.COLLECTION_NAME,
                    with_payload=True,
                    with_vectors=False,
                    limit=128,
                    offset=offset,
                )
                for point in points or []:
                    payload = dict(getattr(point, "payload", {}) or {})
                    classification = str(payload.get("classification_tag") or "INTERNAL").upper()
                    if (
                        str(payload.get("document_id") or "") == document_id
                        and classification in allowed
                    ):
                        return payload
                if offset is None:
                    break
        except Exception as exc:
            raise VisionAnalysisError("Document index is unavailable.", 503) from exc
        raise VisionAnalysisError("Document not found or not authorized.", 403)

    @staticmethod
    def _safe_path(payload: Dict[str, Any]) -> str:
        stored = os.path.basename(str(payload.get("stored_filename") or ""))
        if not stored:
            raise VisionAnalysisError("Document storage reference is unavailable.", 404)
        root = os.path.abspath("uploaded_docs")
        path = os.path.abspath(os.path.join(root, stored))
        if os.path.commonpath([root, path]) != root or not os.path.isfile(path):
            raise VisionAnalysisError("Approved local document is unavailable.", 404)
        if os.path.splitext(path)[1].lower() not in VisionAnalysisService.ALLOWED_EXTENSIONS:
            raise VisionAnalysisError("Unsupported visual document type.", 400)
        return path

    @staticmethod
    def _render_page(path: str, page_number: int) -> tuple[str, int, str]:
        extension = os.path.splitext(path)[1].lower()
        if extension == ".pdf":
            try:
                document = fitz.open(path)
                if page_number < 1 or page_number > len(document):
                    document.close()
                    raise VisionAnalysisError("Requested page does not exist.", 404)
                page = document.load_page(page_number - 1)
                rendered = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False).tobytes("png")
                document.close()
                return base64.b64encode(rendered).decode("ascii"), page_number, "engineering_drawing" if "pid" in os.path.basename(path).lower() else "document"
            except VisionAnalysisError:
                raise
            except Exception as exc:
                raise VisionAnalysisError("Unable to render the PDF page.", 422) from exc
        if page_number != 1:
            raise VisionAnalysisError("Standalone images contain only page 1.", 404)
        try:
            with open(path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode("ascii"), 1, "engineering_drawing" if "pid" in os.path.basename(path).lower() else "image"
        except OSError as exc:
            raise VisionAnalysisError("Unable to load the approved local image.", 422) from exc

    @staticmethod
    def _parse_response(raw: str) -> List[Dict[str, str]]:
        candidate = (raw or "").strip()
        fenced = re.search(r"```(?:json)?\s*(.*?)```", candidate, flags=re.IGNORECASE | re.DOTALL)
        if fenced:
            candidate = fenced.group(1).strip()
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError as exc:
            raise VisionAnalysisError("Vision model returned malformed structured output.", 502) from exc
        observations = parsed.get("observations") if isinstance(parsed, dict) else None
        if not isinstance(observations, list):
            raise VisionAnalysisError("Vision model response did not contain observations.", 502)
        result: List[Dict[str, str]] = []
        for observation in observations:
            if not isinstance(observation, dict) or not str(observation.get("text") or "").strip():
                raise VisionAnalysisError("Vision model returned an invalid observation.", 502)
            result.append({
                "type": "VISION_INFERRED",
                "evidence_type": "VISION_INFERRED",
                "text": str(observation["text"]).strip(),
                "observation": str(observation["text"]).strip(),
            })
        return result

    async def analyze(
        self,
        *,
        document_id: str,
        page: int,
        instruction: str,
        user: User,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        request_id = request_id or uuid.uuid4().hex
        if not instruction or len(instruction.strip()) > 1000:
            raise VisionAnalysisError("A concise visual-analysis instruction is required.", 400)
        payload = self._find_document(document_id, user)
        classification = str(payload.get("classification_tag") or "INTERNAL").upper()
        audit_args = {
            "username": user.username,
            "clearance_tags": [classification],
            "query_or_action": f"visual-analysis:{payload.get('document_name') or payload.get('doc_name')}:{page}",
            "equipment_tag": "N/A",
            "run_id": request_id,
        }
        audit_service.log_entry(event_type="DOCUMENT_VISION_ANALYSIS_STARTED", status="STARTED", **audit_args)
        try:
            path = self._safe_path(payload)
            image_b64, page_number, source_type = self._render_page(path, page)
            model_id = settings.AEGIS_MODEL_VISION or "vision"
            model = self.registry.resolve_model(model_id)
            if model is None:
                raise VisionAnalysisError("Local vision analysis is unavailable.", 503)
            provider = self.registry.get_provider(model.id)
            health = await provider.health_check(model.ollama_tag)
            if str(health.get("status") or "").upper() != "AVAILABLE":
                raise VisionAnalysisError("Local vision analysis is unavailable.", 503)
            raw = await provider.generate(
                model=model.ollama_tag,
                prompt=(
                    "Return JSON only: {\"observations\":[{\"text\":\"...\"}]}. "
                    "Describe only visible content. Do not invent tags, coordinates, confidence, "
                    "relationships, or engineering facts. " + instruction.strip()
                ),
                images=[image_b64],
                timeout=120.0,
            )
            observations = self._parse_response(raw)
            for observation in observations:
                observation["page"] = page_number
            ocr_tags = [
                {"evidence_type": "OCR_EXTRACTED", "text": tag}
                for tag in extract_identifiers(str(payload.get("text") or ""))
            ]
            result = {
                "document_id": document_id,
                "document_name": payload.get("doc_name") or payload.get("document_name"),
                "page": page_number,
                "analysis": observations,
                "source_type": str(payload.get("document_type") or source_type),
                "extraction_method": "vision",
                "classification_tag": classification,
                "model_id": model.ollama_tag,
                "grounding": {
                    "ocr_available": bool(ocr_tags),
                    "visual_analysis_used": True,
                },
                "evidence": ocr_tags + observations,
                "human_verified": False,
            }
            audit_service.log_entry(event_type="DOCUMENT_VISION_ANALYSIS_COMPLETED", status="COMPLETED", **audit_args)
            return result
        except VisionAnalysisError:
            audit_service.log_entry(event_type="DOCUMENT_VISION_ANALYSIS_FAILED", status="FAILED", **audit_args)
            raise
        except ModelProviderError as exc:
            audit_service.log_entry(event_type="DOCUMENT_VISION_ANALYSIS_FAILED", status="FAILED", **audit_args)
            raise VisionAnalysisError("Local vision analysis failed.", 503) from exc
        except Exception as exc:
            audit_service.log_entry(event_type="DOCUMENT_VISION_ANALYSIS_FAILED", status="FAILED", **audit_args)
            raise VisionAnalysisError("Local vision analysis failed.", 503) from exc


vision_analysis_service = VisionAnalysisService()

__all__ = ["VisionAnalysisError", "VisionAnalysisService", "vision_analysis_service"]
