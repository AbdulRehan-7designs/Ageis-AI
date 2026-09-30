import asyncio
import os
import sys
import uuid
from types import SimpleNamespace
from unittest.mock import patch

import pymupdf as fitz

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.auth import User
from app.services.model_registry import RegisteredModel, ModelCapability
from app.services.vision_analysis import VisionAnalysisError, VisionAnalysisService
from app.services.ingestion import IngestionService


class FakeProvider:
    def __init__(self, response='{"observations":[{"text":"A pump-like symbol is visible."}]}'):
        self.response = response
        self.images = None

    async def generate(self, **kwargs):
        self.images = kwargs.get("images")
        return self.response

    async def health_check(self, model_name=None):
        return {"status": "AVAILABLE", "model": model_name}


class FakeRegistry:
    def __init__(self, provider=None, enabled=True):
        self.provider = provider or FakeProvider()
        self.model = RegisteredModel(
            id="vision",
            model="qwen2.5vl:3b",
            ollama_tag="qwen2.5vl:3b",
            capabilities=[ModelCapability.VISION, ModelCapability.DOCUMENT_ANALYSIS],
            enabled=enabled,
        )

    def resolve_model(self, model_id):
        return self.model

    def get_provider(self, model_id):
        return self.provider


class FakeQdrant:
    def __init__(self, payload):
        self.payload = payload

    def scroll(self, **kwargs):
        return [SimpleNamespace(payload=self.payload)], None


class FakeIngestion:
    COLLECTION_NAME = "industrial_docs"

    def __init__(self, payload):
        self.qdrant_client = FakeQdrant(payload)


def _fixture():
    os.makedirs("uploaded_docs", exist_ok=True)
    name = f"vision-test-{uuid.uuid4().hex}.pdf"
    path = os.path.join("uploaded_docs", name)
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), "P-204 inspection drawing")
    document.save(path)
    document.close()
    return name, path


def test_authorized_pdf_page_analysis_preserves_provenance():
    filename, path = _fixture()
    document_id = uuid.uuid4().hex
    payload = {
        "document_id": document_id,
        "doc_name": "inspection.pdf",
        "stored_filename": filename,
        "classification_tag": "INTERNAL",
        "text": "OCR extracted P-204",
    }
    provider = FakeProvider()
    service = VisionAnalysisService(FakeIngestion(payload), FakeRegistry(provider))
    try:
        with patch("app.services.vision_analysis.audit_service.log_entry"):
            result = asyncio.run(service.analyze(
                document_id=document_id,
                page=1,
                instruction="Describe the visible drawing.",
                user=User(username="engineer", role="ENGINEER", clearance_tags=["INTERNAL"]),
            ))
        assert result["document_id"] == document_id
        assert result["page"] == 1
        assert result["extraction_method"] == "vision"
        assert result["grounding"]["ocr_available"] is True
        assert any(item["text"] == "P-204" for item in result["evidence"])
        assert provider.images
    finally:
        os.remove(path)


def test_secret_document_is_denied_before_model():
    filename, path = _fixture()
    payload = {
        "document_id": "secret-id",
        "doc_name": "secret.pdf",
        "stored_filename": filename,
        "classification_tag": "SECRET",
    }
    provider = FakeProvider()
    service = VisionAnalysisService(FakeIngestion(payload), FakeRegistry(provider))
    try:
        with patch("app.services.vision_analysis.audit_service.log_entry"):
            try:
                asyncio.run(service.analyze(
                    document_id="secret-id", page=1, instruction="Inspect it.",
                    user=User(username="operator", role="OPERATOR", clearance_tags=["INTERNAL"]),
                ))
                assert False, "expected authorization denial"
            except VisionAnalysisError as exc:
                assert exc.status_code == 403
        assert provider.images is None
    finally:
        os.remove(path)


def test_invalid_page_and_malformed_response_are_controlled():
    filename, path = _fixture()
    payload = {
        "document_id": "doc-id",
        "doc_name": "drawing.pdf",
        "stored_filename": filename,
        "classification_tag": "INTERNAL",
    }
    try:
        service = VisionAnalysisService(FakeIngestion(payload), FakeRegistry(FakeProvider("not-json")))
        with patch("app.services.vision_analysis.audit_service.log_entry"):
            try:
                asyncio.run(service.analyze(
                    document_id="doc-id", page=2, instruction="Inspect it.",
                    user=User(username="engineer", role="ENGINEER", clearance_tags=["INTERNAL"]),
                ))
                assert False
            except VisionAnalysisError as exc:
                assert exc.status_code == 404
            try:
                asyncio.run(service.analyze(
                    document_id="doc-id", page=1, instruction="Inspect it.",
                    user=User(username="engineer", role="ENGINEER", clearance_tags=["INTERNAL"]),
                ))
                assert False
            except VisionAnalysisError as exc:
                assert exc.status_code == 502
        with patch("app.services.vision_analysis.audit_service.log_entry"):
            try:
                asyncio.run(service.analyze(
                    document_id="../outside", page=1, instruction="Inspect it.",
                    user=User(username="engineer", role="ENGINEER", clearance_tags=["INTERNAL"]),
                ))
                assert False
            except VisionAnalysisError as exc:
                assert exc.status_code == 400
    finally:
        os.remove(path)


def test_engineering_metadata_is_conservative_and_does_not_infer_relationships():
    service = IngestionService.__new__(IngestionService)
    metadata = service._infer_document_metadata(
        "P&ID-204.pdf",
        "P-204 PSV-204 XV-301",
    )
    assert metadata["source_type"] == "P_AND_ID"
    assert [item["tag"] for item in metadata["engineering_tags"]] == ["P-204", "PSV-204", "XV-301"]
    assert "relationships" not in metadata
    generic = service._infer_document_metadata("inspection.pdf", "PUMP VALVE")
    assert generic["document_type"] == "technical_document"
