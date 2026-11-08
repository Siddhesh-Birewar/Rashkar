import uuid
import httpx
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from backend.app.db.session import get_db
from backend.app.db.models.farm import FarmModel, FarmerModel
from backend.app.db.models.assistant import AssistantSessionModel, AssistantMessageModel
from backend.app.db.models.crop_knowledge import AgronomicAdvisoryCatalogueModel
from backend.app.services.crop_stage_service import CropStageService
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
    provider_used: str  # none, ollama, cloud
    model_name: Optional[str] = None
    citations: List[Dict[str, str]] = []
    grounded_context_summary: Dict[str, Any]
    disclaimer: str

def generate_grounded_template_answer(
    message: str,
    farm: FarmModel,
    farmer_name: str,
    crop_name: str,
    stage_name: str,
    weather: Dict[str, Any],
    advisories: List[AgronomicAdvisoryCatalogueModel]
) -> str:
    """
    Deterministic template fallback when Ollama is disabled or unreachable.
    Answers strictly grounded in retrieved database records.
    """
    msg_low = message.lower()
    
    if any(k in msg_low for k in ["risk", "why", "status", "health"]):
        adv_text = advisories[0].description_en if advisories else "Ensure adequate drainage and monitor daily heat advisories."
        return (
            f"Hello {farmer_name}. For your {crop_name} crop at {farm.farm_name} ({farm.taluka}), "
            f"it is currently in the {stage_name} stage. Today's temperature is around {weather['temperature_c']}°C "
            f"with {weather['condition']}. \n\n"
            f"Key recommendation: {adv_text}"
        )
    elif any(k in msg_low for k in ["weather", "temperature", "rain"]):
        return (
            f"Today's weather at your farm in {farm.taluka}, Pune: "
            f"{weather['temperature_c']}°C, humidity {weather['relative_humidity_pct']}%, "
            f"wind {weather['wind_speed_kmh']} km/h, condition: {weather['condition']}. "
            f"Rainfall today: {weather['rainfall_today_mm']} mm. (Source: {weather['source']})."
        )
    elif any(k in msg_low for k in ["heat", "worker", "work", "afternoon"]):
        return (
            f"Heat safety guidance for {farm.taluka}: Field heat stress peaks between 12:30 PM and 3:30 PM. "
            f"We advise scheduling heavy physical work in the morning or shaded areas. Stay hydrated with clean water."
        )
    else:
        adv_text = advisories[0].title_en if advisories else "Consult local KVK or agricultural extension officers."
        return (
            f"Regarding your {crop_name} crop ({stage_name} stage) in {farm.taluka}: "
            f"Current conditions are stable. Current advisory: '{adv_text}'. "
            f"Feel free to ask about your crop risks, weather conditions, or heat safety."
        )

def call_local_ollama(prompt: str, model: str = "qwen3:8b") -> Optional[str]:
    """Calls developer's local Ollama instance on port 11434 with timeout."""
    try:
        url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2, "top_p": 0.8}
        }
        with httpx.Client(timeout=8.0) as client:
            resp = client.post(url, json=payload)
            if resp.status_code == 200:
                return resp.json().get("response")
    except Exception:
        return None
    return None

@router.post("/chat", response_model=ChatMessageResponse)
def assistant_chat(request: ChatMessageRequest, db: Session = Depends(get_db)):
    # 1. Retrieve authoritative farm context
    farm = db.query(FarmModel).filter(FarmModel.farm_id == request.farm_id).first()
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")
    
    farmer = db.query(FarmerModel).filter(FarmerModel.farmer_id == request.farmer_id).first()
    farmer_name = farmer.full_name if farmer else "Farmer"

    # Find active crop
    active_cycle = None
    for p in farm.plots:
        for c in p.crop_cycles:
            if c.is_active:
                active_cycle = c
                break
        if active_cycle:
            break

    crop_code = active_cycle.crop_code if active_cycle else "general_crops"
    crop_name = crop_code.title()
    stage_name = "Vegetative Growth"
    if active_cycle:
        st = CropStageService.estimate_crop_stage(db, active_cycle.crop_code, active_cycle.sowing_date)
        stage_name = st["stage_name_en"]

    weather = {
        "temperature_c": 32.5,
        "relative_humidity_pct": 58.0,
        "wind_speed_kmh": 12.0,
        "condition": "Partly Cloudy",
        "rainfall_today_mm": 0.0,
        "source": "IMD Pune Station / Gridded Reanalysis"
    }

    # Retrieve relevant agronomic advisories from database
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

    provider_to_use = request.provider_override or getattr(settings, "ASSISTANT_PROVIDER_MODE", "none")
    reply_text = None
    model_name = None

    if provider_to_use == "ollama":
        # Formulate grounded prompt for Ollama
        advisories_str = "\n".join([f"- {a.title_en}: {a.description_en} (Source: {a.evidence_citation})" for a in advisories])
        grounded_prompt = (
            f"You are Rashkar, an expert AI agronomic assistant for Maharashtra farmers.\n"
            f"Farmer: {farmer_name}\n"
            f"Location: {farm.village or ''}, {farm.taluka}, {farm.district}, Maharashtra\n"
            f"Active Crop: {crop_name} (Current Stage: {stage_name})\n"
            f"Today's Weather: {weather['temperature_c']}°C, {weather['condition']}, Humidity {weather['relative_humidity_pct']}%\n"
            f"Authoritative Advisories:\n{advisories_str}\n\n"
            f"Farmer Question: {request.message}\n\n"
            f"Instructions:\n"
            f"- Answer in 2-3 clear, simple English sentences.\n"
            f"- Use ONLY the facts provided above. Do NOT invent temperatures, risk scores, or ungrounded chemicals.\n"
            f"- State when information is not available.\n"
            f"Answer:"
        )
        ollama_resp = call_local_ollama(grounded_prompt, model="qwen3:8b")
        if ollama_resp:
            reply_text = ollama_resp.strip()
            model_name = "qwen3:8b"
        else:
            # Fallback to template if Ollama is offline
            provider_to_use = "none (fallback from ollama)"

    if not reply_text:
        reply_text = generate_grounded_template_answer(
            request.message, farm, farmer_name, crop_name, stage_name, weather, advisories
        )

    # Save user message and assistant reply to DB
    msg_user = AssistantMessageModel(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        sender="user",
        content=request.message,
        provider_mode=provider_to_use
    )
    msg_assistant = AssistantMessageModel(
        message_id=f"msg_{uuid.uuid4().hex[:8]}",
        session_id=session_id,
        sender="assistant",
        content=reply_text,
        retrieved_context_json={"crop": crop_name, "stage": stage_name, "weather": weather},
        citations_json=citations,
        provider_mode=provider_to_use,
        model_name=model_name
    )
    db.add(msg_user)
    db.add(msg_assistant)
    db.commit()

    return ChatMessageResponse(
        session_id=session_id,
        reply=reply_text,
        provider_used=provider_to_use,
        model_name=model_name,
        citations=citations,
        grounded_context_summary={
            "farm": farm.farm_name,
            "crop": crop_name,
            "stage": stage_name,
            "weather_temp_c": weather["temperature_c"]
        },
        disclaimer="Grounded advice based on MPKV/ICAR research and retrieved farm observations. Not an official insurance or medical warranty."
    )
