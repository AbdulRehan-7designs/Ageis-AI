from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

router = APIRouter()

class IngestResponse(BaseModel):
    filename: str
    chunks_indexed: int
    classification_tag: str
    status: str

@router.post("/document/upload", response_model=IngestResponse)
async def upload_document(file: UploadFile = File(...)):
    return IngestResponse(
        filename=file.filename,
        chunks_indexed=12,
        classification_tag="INTERNAL",
        status="SUCCESS_INDEXED_LOCAL_QDRANT"
    )
