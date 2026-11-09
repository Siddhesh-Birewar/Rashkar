import uuid
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmModel, FarmerModel
from backend.app.db.models.assistant import AssistantSessionModel, AssistantMessageModel
from backend.app.db.models.crop_knowledge import AgronomicAdvisoryCatalogueModel
from backend.app.services.crop_stage_service import CropStageService
from backend.app.services.ollama_agent_service import OllamaAgentService
from backend.app.core.config import settings
from backend.app.core.timezone import now_ist

router = APIRouter()

class ChatMessageRequest(BaseModel):
    farmer_id: str = Field(..., json_schema_extra={"example": "farmer_demo_01"})
    farm_id: str = Field(..., json_schema_extra={"example": "farm_demo_pune_01"})
    message: str = Field(..., json_schema_extra={"example": "Why is my crop at risk today?"})
    session_id: Optional[str] = None
    provider_override: Optional[str] = None  # none, ollama, cloud

class ChatMessageResponse(BaseModel):
    session_id: str
    reply: str
    provider_used: str  # none, ollama, cloud, deterministic_grounded_fallback
    model_name: Optional[str] = None
    citations: List[Dict[str, str]] = []
    grounded_context_summary: Dict[str, Any]
    disclaimer: str

@router.get("/context")
def get_assistant_context(
    farm_id: str = Query("farm_demo_pune_01"),
    farmer_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Returns the grounded farm profile summary chip for the Ask Rashkar screen."""
    ctx = OllamaAgentService.assemble_farm_context(db, farm_id=farm_id, farmer_id=farmer_id)
    if "error" in ctx:
        raise HTTPException(status_code=404, detail=ctx["error"])

    chip_label = f"Using your farm information: {ctx.get('primary_crop')} ({ctx.get('primary_stage')}) · {ctx.get('taluka')} · {ctx.get('total_area_acres')} acres"
    return {
        "farm_id": farm_id,
        "chip_label": chip_label,
        "context": ctx
    }

@router.post("/chat", response_model=ChatMessageResponse)
def assistant_chat(request: ChatMessageRequest, db: Session = Depends(get_db)):
    # 1. Retrieve authoritative farm context
    ctx = OllamaAgentService.assemble_farm_context(db, farm_id=request.farm_id, farmer_id=request.farmer_id)
    if "error" in ctx:
        raise HTTPException(status_code=404, detail=ctx["error"])

    # 2. Citations from advisories
    crop_code = ctx.get("primary_crop", "General").lower()
    advisories = db.query(AgronomicAdvisoryCatalogueModel).filter(
        AgronomicAdvisoryCatalogueModel.crop_code == crop_code
    ).all()

    citations = [
        {"source_id": adv.action_id, "title": adv.title_en, "citation": adv.evidence_citation}
        for adv in advisories[:2]
    ]

    # Session management
    session_id = request.session_id
    if not session_id:
        session_id = f"sess_{uuid.uuid4().hex[:8]}"
        new_sess = AssistantSessionModel(
            session_id=session_id,
            farmer_id=request.farmer_id,
            farm_id=request.farm_id
        )
        db.add(new_sess)
        db.flush()

    # Generate grounded response
    chat_result = OllamaAgentService.generate_chat_response(
        message=request.message,
        context=ctx,
        timeout=15.0
    )

    reply_text = chat_result["reply"]
    provider_used = chat_result["provider_used"]
    model_name = chat_result.get("model_name")

    # Record message history
    msg_user = AssistantMessageModel(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        sender="user",
        content=request.message,
        provider_mode=provider_used
    )
    msg_assistant = AssistantMessageModel(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        sender="assistant",
        content=reply_text,
        retrieved_context_json=ctx,
        citations_json=citations,
        provider_mode=provider_used,
        model_name=model_name
    )
    db.add(msg_user)
    db.add(msg_assistant)
    db.commit()

    return ChatMessageResponse(
        session_id=session_id,
        reply=reply_text,
        provider_used=provider_used,
        model_name=model_name,
        citations=citations,
        grounded_context_summary={
            "farm": ctx.get("farm_name"),
            "crop": ctx.get("primary_crop"),
            "stage": ctx.get("primary_stage"),
            "weather_temp_c": ctx.get("weather", {}).get("air_temp_c")
        },
        disclaimer="Grounded advice based on MPKV/ICAR research and retrieved farm observations. Not an official insurance or medical warranty."
    )

@router.post("/chat-stream")
def assistant_chat_stream(request: ChatMessageRequest, db: Session = Depends(get_db)):
    """Server-Sent Events (SSE) streaming endpoint for real-time token delivery."""
    ctx = OllamaAgentService.assemble_farm_context(db, farm_id=request.farm_id, farmer_id=request.farmer_id)
    if "error" in ctx:
        raise HTTPException(status_code=404, detail=ctx["error"])

    return StreamingResponse(
        OllamaAgentService.generate_chat_stream(
            message=request.message,
            context=ctx,
            timeout=30.0
        ),
        media_type="text/event-stream"
    )
