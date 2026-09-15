import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from app.services.ingestion import ingestion_service
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    classification_tag: str
    status: str
    message: str

@router.post("/document/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    classification_tag: str = "INTERNAL"
):
    """
    Upload and ingest a PDF document into the hybrid RAG system.
    
    - Parses PDF with fitz
    - Chunks text intelligently (400 tokens, 50 overlap)
    - Embeds with dense (bge-m3) + sparse (BM25)
    - Upserts to Qdrant collection
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    try:
        # Save uploaded file to temp location
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        logger.info(f"Ingesting document: {file.filename}")
        
        # Run ingestion pipeline
        stats = ingestion_service.ingest_pdf(
            pdf_path=tmp_path,
            doc_name=file.filename,
            classification_tag=classification_tag,
        )
        
        logger.info(f"Ingestion complete: {stats}")
        
        return IngestResponse(
            filename=file.filename,
            chunks_indexed=stats.get("total_chunks", 0),
            classification_tag=classification_tag,
            status="SUCCESS_INDEXED_HYBRID_RAG",
            message=f"Ingested {stats.get('total_chunks', 0)} chunks with {stats.get('total_tables', 0)} tables detected"
        )
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")
    
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
