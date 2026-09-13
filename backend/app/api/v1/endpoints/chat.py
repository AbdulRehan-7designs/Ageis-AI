from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Optional
from app.services.agent_orchestrator import agent_orchestrator

router = APIRouter()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    classification_filter: Optional[str] = "INTERNAL"
    model_override: Optional[str] = None

class Citation(BaseModel):
    document: str
    page: int
    tag: str
    snippet: str

class ReasoningStep(BaseModel):
    step_number: int
    title: str
    description: str
    status: str

class EquipmentDetail(BaseModel):
    tag: str
    status: str
    type: str
    location: str
    vibration_val: str
    vibration_status: str
    threshold: str
    temp: str

class RecommendedAction(BaseModel):
    title: str
    sop_code: str
    requires_approval: bool
    steps: List[str]
    why_reasoning: List[str]

class ChatResponse(BaseModel):
    reply_title: str
    diagnosis_summary: str
    model_used: str
    classification_level: str
    execution_time_sec: float
    citations: List[Citation]
    reasoning_trace: List[ReasoningStep]
    equipment_details: Optional[EquipmentDetail] = None
    recommended_action: RecommendedAction
    hitl_approval_required: bool
    risk_score: float

@router.post("/chat", response_model=ChatResponse)
async def process_chat(request: ChatRequest):
    result = await agent_orchestrator.process_query(
        user_message=request.message,
        model_override=request.model_override
    )
    return ChatResponse(**result)
