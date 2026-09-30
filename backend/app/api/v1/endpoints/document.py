import os
import tempfile
import logging
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, Header
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.ingestion import ingestion_service
from app.services.audit_service import audit_service
from app.services.vision_analysis import VisionAnalysisError, vision_analysis_service
from app.core.auth import User, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class IngestResponse(BaseModel):
    document_id: Optional[str] = None
    filename: str
    stored_filename: Optional[str] = None
    chunks_indexed: int
    classification_tag: str
    document_type: Optional[str] = None
    drawing_type: Optional[str] = None
    object_tag: Optional[str] = None
    equipment_tags: List[str] = []
    related_tags: List[str] = []
    page_count: int = 0
    total_tables: int = 0
    evidence_ready: bool = False
    metadata: Optional[dict] = None
    status: str
    message: str


class BatchIngestResponse(BaseModel):
    count: int
    total_chunks: int
    documents: List[IngestResponse]
    status: str
    message: str


class VisualAnalysisRequest(BaseModel):
    instruction: str
    page: int = 1


class VisualAnalysisResponse(BaseModel):
    document_id: str
    document_name: Optional[str] = None
    page: int
    analysis: List[dict]
    source_type: str
    extraction_method: str
    classification_tag: str
    model_id: str
    grounding: dict
    evidence: List[dict]
    human_verified: bool = False


def _safe_stored_name(original: str) -> str:
    base = os.path.basename(original or "document.pdf").replace("..", "")
    return f"{uuid.uuid4().hex[:8]}_{base}"


def _ingest_bytes(filename: str, contents: bytes, classification_tag: str, username: str = "system") -> IngestResponse:
    extension = os.path.splitext(filename or "")[1].lower()
    if extension not in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        raise HTTPException(status_code=400, detail=f"Unsupported document type ({filename})")
    if not contents:
        raise HTTPException(status_code=400, detail=f"Empty upload ({filename})")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=extension, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        safe_name = _safe_stored_name(filename)
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        shutil.copy(tmp_path, os.path.join(UPLOAD_DIR, safe_name))

        if extension == ".pdf":
            audit_service.log_entry(
                event_type="DOCUMENT_OCR_STARTED", username=username,
                clearance_tags=[classification_tag], query_or_action=filename,
            )
            stats = ingestion_service.ingest_pdf(
                pdf_path=tmp_path, doc_name=filename,
                classification_tag=classification_tag, stored_filename=safe_name,
            )
            if stats.get("ocr_pages"):
                audit_service.log_entry(
                    event_type="DOCUMENT_OCR_COMPLETED", username=username,
                    clearance_tags=[classification_tag], query_or_action=filename,
                    status="COMPLETED",
                )
        else:
            audit_service.log_entry(
                event_type="DOCUMENT_OCR_STARTED", username=username,
                clearance_tags=[classification_tag], query_or_action=filename,
            )
            stats = ingestion_service.ingest_image(
                image_path=tmp_path, doc_name=filename,
                classification_tag=classification_tag, stored_filename=safe_name,
            )
            audit_service.log_entry(
                event_type="DOCUMENT_OCR_COMPLETED", username=username,
                clearance_tags=[classification_tag], query_or_action=filename,
                status="COMPLETED",
            )
        metadata = stats.get("metadata") or {}
        return IngestResponse(
            document_id=metadata.get("content_hash"),
            filename=filename,
            stored_filename=safe_name,
            chunks_indexed=stats.get("total_chunks", 0),
            classification_tag=classification_tag,
            document_type=metadata.get("document_type"),
            drawing_type=metadata.get("drawing_type"),
            object_tag=metadata.get("object_tag"),
            equipment_tags=metadata.get("equipment_tags", []),
            related_tags=metadata.get("related_tags", []),
            page_count=stats.get("page_count", metadata.get("page_count", 0)),
            total_tables=stats.get("total_tables", metadata.get("table_count", 0)),
            evidence_ready=bool(stats.get("evidence_ready")),
            metadata=metadata,
            status="SUCCESS_INDEXED_HYBRID_RAG",
            message=(
                f"Ingested {stats.get('total_chunks', 0)} chunks "
                f"with {stats.get('total_tables', 0)} tables detected"
            ),
        )
    except Exception:
        if extension in {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
            audit_service.log_entry(
                event_type="DOCUMENT_OCR_FAILED", username=username,
                clearance_tags=[classification_tag], query_or_action=filename,
                status="FAILED",
            )
        raise
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


def _resolve_pdf_path(stored_filename: Optional[str] = None, doc_name: Optional[str] = None) -> Optional[str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    if stored_filename:
        candidate = os.path.join(UPLOAD_DIR, os.path.basename(stored_filename))
        if os.path.isfile(candidate):
            return candidate
    if doc_name:
        original = os.path.basename(doc_name)
        direct = os.path.join(UPLOAD_DIR, original)
        if os.path.isfile(direct):
            return direct
        suffix = f"_{original}"
        try:
            matches = [
                os.path.join(UPLOAD_DIR, name)
                for name in os.listdir(UPLOAD_DIR)
                if name.endswith(suffix) or name == original
            ]
            if matches:
                matches.sort(key=os.path.getmtime, reverse=True)
                return matches[0]
        except FileNotFoundError:
            return None
    return None


@router.post("/document/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    classification_tag: str = "INTERNAL",
    current_user: User = Depends(get_current_user),
):
    if classification_tag.upper() not in {tag.upper() for tag in current_user.clearance_tags}:
        raise HTTPException(status_code=403, detail="User clearance does not permit this classification.")
    try:
        contents = await file.read()
        return _ingest_bytes(file.filename, contents, classification_tag, current_user.username)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Ingestion failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(exc)}") from exc


@router.post("/document/upload-batch", response_model=BatchIngestResponse)
async def upload_documents(
    files: List[UploadFile] = File(...),
    classification_tag: str = "INTERNAL",
    current_user: User = Depends(get_current_user),
):
    if classification_tag.upper() not in {tag.upper() for tag in current_user.clearance_tags}:
        raise HTTPException(status_code=403, detail="User clearance does not permit this classification.")
    documents: List[IngestResponse] = []
    errors: List[str] = []
    for upload in files:
        try:
            contents = await upload.read()
            documents.append(_ingest_bytes(upload.filename, contents, classification_tag, current_user.username))
        except HTTPException as exc:
            errors.append(f"{upload.filename}: {exc.detail}")
        except Exception as exc:
            logger.error("Batch item failed (%s): %s", upload.filename, exc, exc_info=True)
            errors.append(f"{upload.filename}: {exc}")

    if not documents:
        raise HTTPException(status_code=400, detail="; ".join(errors) or "No PDFs ingested")

    total = sum(item.chunks_indexed for item in documents)
    message = f"Indexed {len(documents)} document(s) into the same knowledge base ({total} chunks)."
    if errors:
        message += " Some files were skipped: " + "; ".join(errors)
    return BatchIngestResponse(
        count=len(documents),
        total_chunks=total,
        documents=documents,
        status="SUCCESS_INDEXED_HYBRID_RAG",
        message=message,
    )


@router.get("/document/list")
async def list_documents(
    q: Optional[str] = Query(default=None, min_length=1),
    current_user: User = Depends(get_current_user),
):
    return {
        "documents": ingestion_service.list_documents(
            allowed_tags=current_user.clearance_tags,
            query=q,
        )
    }


@router.get("/document/file")
async def serve_document(
    stored_filename: Optional[str] = Query(default=None),
    doc_name: Optional[str] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    authorized = ingestion_service.list_documents(
        allowed_tags=current_user.clearance_tags,
        query=doc_name,
    )
    if stored_filename and not any(
        item.get("stored_filename") == os.path.basename(stored_filename)
        for item in authorized
    ):
        raise HTTPException(status_code=403, detail="User clearance does not permit this document.")
    if doc_name and not authorized:
        raise HTTPException(status_code=403, detail="User clearance does not permit this document.")
    path = _resolve_pdf_path(stored_filename=stored_filename, doc_name=doc_name)
    if not path:
        raise HTTPException(status_code=404, detail="PDF not found on disk")
    return FileResponse(path, media_type="application/pdf", filename=os.path.basename(path))


@router.post("/document/{document_id}/visual-analysis", response_model=VisualAnalysisResponse)
async def analyze_document_page(
    document_id: str,
    request: VisualAnalysisRequest,
    current_user: User = Depends(get_current_user),
    x_request_id: Optional[str] = Header(default=None),
):
    try:
        return await vision_analysis_service.analyze(
            document_id=document_id,
            page=request.page,
            instruction=request.instruction,
            user=current_user,
            request_id=x_request_id,
        )
    except VisionAnalysisError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
