from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    classification_filter: Optional[str] = "INTERNAL"
    model_override: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    model_used: str
    classification_level: str
    citations: List[dict]
    hitl_approval_required: bool
    risk_score: float

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    # Skeleton implementation for Agentic RAG + Model Router
    return ChatResponse(
        reply=f"AegisAI Skeleton Response: Received '{request.message}'. System is operating in air-gapped sovereign mode.",
        model_used=request.model_override or "qwen2.5:7b",
        classification_level=request.classification_filter or "INTERNAL",
        citations=[
            {
                "document": "SOP_Turbine_Safety_v4.pdf",
                "page": 14,
                "tag": "CONFIDENTIAL",
                "snippet": "Section 4.2: Maximum operational pressure threshold must not exceed 450 PSI."
            }
        ],
        hitl_approval_required=False,
        risk_score=0.12
    )
