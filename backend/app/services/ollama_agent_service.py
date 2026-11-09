import json
import httpx
from typing import Dict, Any, Generator, Optional, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.db.models.farm import FarmModel, FarmerModel, SoilProfileModel
from backend.app.db.models.crop_knowledge import CropStageReferenceModel, AgronomicAdvisoryCatalogueModel
from backend.app.services.weather_service import WeatherService
from backend.app.services.wbgt_solver import calculate_wbgt
from backend.app.services.crop_stage_service import CropStageService
from backend.app.services.opportunity_feasibility_engine import OpportunityFeasibilityEngine
from backend.app.schemas.income import FarmerResourceProfile

OLLAMA_API_URL = "http://127.0.0.1:11434/api/generate"
DEFAULT_MODEL = "qwen3:8b"

class OllamaAgentService:
    @staticmethod
    def assemble_farm_context(db: Session, farm_id: str, farmer_id: Optional[str] = None) -> Dict[str, Any]:
        """Gathers authoritative parcel, phenology, weather, soil, and income data."""
        farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
        if not farm:
            return {"error": "Farm not found"}

        farmer = db.query(FarmerModel).filter(FarmerModel.farmer_id == (farmer_id or farm.owner_id)).first()
        farmer_name = farmer.full_name if farmer else "Farmer"
        district = farm.district or "Pune"
        taluka = farm.taluka or "Haveli"
        village = farm.village or ""

        # Plots and Active Crop Cycles
        active_cycles_info = []
        primary_crop = "General Crops"
        primary_stage = "Vegetative"
        primary_critical_temp = 35.0

        if farm.plots:
            for plot in farm.plots:
                for cycle in plot.crop_cycles:
                    if cycle.is_active:
                        stage_data = CropStageService.estimate_crop_stage(db, cycle.crop_code, cycle.sowing_date)
                        stage_name = stage_data.get("stage_name_en", "Vegetative")
                        crit_t = stage_data.get("critical_temp_c", 35.0)

                        active_cycles_info.append({
                            "crop": cycle.crop_code.capitalize(),
                            "variety": cycle.variety_name or "Local Hybrid",
                            "stage": stage_name,
                            "sowing_date": str(cycle.sowing_date),
                            "critical_temp_c": crit_t
                        })
                        if primary_crop == "General Crops":
                            primary_crop = cycle.crop_code.capitalize()
                            primary_stage = stage_name
                            primary_critical_temp = crit_t

        # Weather & WBGT
        lat = farm.latitude or 20.08
        lon = farm.longitude or 74.08
        weather_data = {}
        wbgt_val = 28.0
        try:
            w_res = WeatherService.get_current_weather_and_forecast(lat=lat, lon=lon)
            curr = w_res.get("current", {})
            t_air = float(curr.get("temperature_c", 32.0))
            rh = float(curr.get("humidity_pct", 55.0))
            wind = float(curr.get("wind_speed_ms", 1.5))
            solar = float(curr.get("solar_radiation_wm2", 650.0))

            wbgt_calc = calculate_wbgt(
                temp_c=t_air, rh_pct=rh, wind_speed_ms=wind, solar_irradiance_wm2=solar, in_sun=True
            )
            wbgt_val = wbgt_calc.get("wbgt_estimated_c", 28.0)
            weather_data = {
                "air_temp_c": t_air,
                "humidity_pct": rh,
                "wind_ms": wind,
                "solar_radiation_wm2": solar,
                "wbgt_sun_c": wbgt_val,
                "condition": curr.get("condition", "Clear Sky")
            }
        except Exception:
            weather_data = {"air_temp_c": 32.0, "humidity_pct": 55.0, "wbgt_sun_c": 28.0, "condition": "Normal"}

        # Soil profile
        soil_info = "Medium black soil (clay loam, pH ~7.6)"
        if farm.soil_profile:
            sp = farm.soil_profile
            soil_info = f"pH {sp.ph or 7.5}, Clay {sp.clay_pct or 45}%, Organic Carbon {sp.organic_carbon_pct or 0.55}% ({sp.data_provenance})"

        # Top 2 Income Opportunities for quick grounding
        income_opps = []
        try:
            prof = FarmerResourceProfile(
                available_investment_inr=15000.0,
                water_availability="seasonal_canal",
                available_land_acres=0.5,
                family_labor_hours_day=2.0
            )
            discovered = OpportunityFeasibilityEngine.discover_and_rank_opportunities(prof)
            for d in discovered[:2]:
                income_opps.append({
                    "title": d.opportunity.title,
                    "benefit": d.primary_benefit_label,
                    "status": d.suitability_verdict
                })
        except Exception:
            pass

        return {
            "farmer_name": farmer_name,
            "farm_name": farm.farm_name,
            "district": district,
            "taluka": taluka,
            "village": village,
            "total_area_acres": farm.total_area_acres or 2.5,
            "crops": active_cycles_info,
            "primary_crop": primary_crop,
            "primary_stage": primary_stage,
            "critical_temp_c": primary_critical_temp,
            "weather": weather_data,
            "soil": soil_info,
            "income_opportunities": income_opps,
            "assessed_at": datetime.now(timezone.utc).isoformat()
        }

    @staticmethod
    def build_system_prompt(context: Dict[str, Any]) -> str:
        crops_str = ", ".join([f"{c['crop']} ({c['stage']})" for c in context.get("crops", [])]) or context.get("primary_crop", "Crops")
        w = context.get("weather", {})
        income_str = "; ".join([f"{i['title']} ({i['benefit']})" for i in context.get("income_opportunities", [])])

        return (
            f"You are Rashkar Assistant, a practical, grounded agricultural and heat-safety AI for Maharashtra smallholder farmers.\n"
            f"You are conversing with {context.get('farmer_name', 'Farmer')}, who operates {context.get('farm_name', 'Farm')} "
            f"in {context.get('taluka')}, {context.get('district')}, Maharashtra (Total Area: {context.get('total_area_acres')} acres).\n\n"
            f"REAL-TIME FARM CONDITIONS:\n"
            f"- Active Crops: {crops_str}\n"
            f"- Crop Thermal Tolerance Limit: {context.get('critical_temp_c')}°C\n"
            f"- Current Weather: Air Temp {w.get('air_temp_c')}°C, Humidity {w.get('humidity_pct')}%, Solar WBGT {w.get('wbgt_sun_c')}°C, Condition: {w.get('condition')}\n"
            f"- Soil Characteristics: {context.get('soil')}\n"
            f"- Suitable Extra Income Options: {income_str}\n\n"
            f"BEHAVIOR RULES:\n"
            f"1. Keep answers concise (2 to 4 sentences), clear, and direct. Suitable for busy farmers.\n"
            f"2. Always anchor your answers in the specific facts above. Mention the farmer's crop, village/taluka, and current temperature.\n"
            f"3. If WBGT > 28°C or Air Temp > 38°C, actively remind the farmer to avoid peak noon labor and hydrate regularly.\n"
            f"4. Never invent chemical dosage rates or guarantee insurance claim approvals. If asked about insurance, refer to PMFBY filing protocol.\n"
            f"5. Maintain a respectful, encouraging tone."
        )

    @classmethod
    def generate_chat_response(
        cls,
        message: str,
        context: Dict[str, Any],
        model: str = DEFAULT_MODEL,
        timeout: float = 30.0
    ) -> Dict[str, Any]:
        """Generates grounded response using Ollama with automatic template fallback."""
        sys_prompt = cls.build_system_prompt(context)
        full_prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n"

        try:
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.85,
                    "num_predict": 180
                }
            }
            with httpx.Client(timeout=timeout) as client:
                res = client.post(OLLAMA_API_URL, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data.get("response", "").strip()
                    if response_text:
                        return {
                            "reply": response_text,
                            "provider_used": "ollama",
                            "model_name": model,
                            "is_fallback": False
                        }
        except Exception:
            pass

        # Deterministic Grounded Fallback if Ollama is unreachable
        return {
            "reply": cls._generate_deterministic_fallback(message, context),
            "provider_used": "deterministic_grounded_fallback",
            "model_name": "rule_based_agronomic_engine",
            "is_fallback": True
        }

    @classmethod
    def generate_chat_stream(
        cls,
        message: str,
        context: Dict[str, Any],
        model: str = DEFAULT_MODEL,
        timeout: float = 40.0
    ) -> Generator[str, None, None]:
        """Yields Server-Sent Events (SSE) data stream."""
        sys_prompt = cls.build_system_prompt(context)
        full_prompt = f"<|im_start|>system\n{sys_prompt}<|im_end|>\n<|im_start|>user\n{message}<|im_end|>\n<|im_start|>assistant\n"

        try:
            payload = {
                "model": model,
                "prompt": full_prompt,
                "stream": True,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.85,
                    "num_predict": 180
                }
            }
            with httpx.Client(timeout=timeout) as client:
                with client.stream("POST", OLLAMA_API_URL, json=payload) as stream_resp:
                    if stream_resp.status_code == 200:
                        for line in stream_resp.iter_lines():
                            if line:
                                try:
                                    chunk_json = json.loads(line)
                                    token = chunk_json.get("response", "")
                                    done = chunk_json.get("done", False)
                                    yield f"data: {json.dumps({'token': token, 'done': done, 'provider': 'ollama'})}\n\n"
                                    if done:
                                        return
                                except Exception:
                                    continue
                        return
        except Exception:
            pass

        # Stream fallback word by word
        fallback_text = cls._generate_deterministic_fallback(message, context)
        words = fallback_text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            done = (i == len(words) - 1)
            yield f"data: {json.dumps({'token': token, 'done': done, 'provider': 'fallback'})}\n\n"

    @staticmethod
    def _generate_deterministic_fallback(message: str, context: Dict[str, Any]) -> str:
        msg = message.lower()
        crop = context.get("primary_crop", "Crop")
        stage = context.get("primary_stage", "Vegetative")
        taluka = context.get("taluka", "Maharashtra")
        w = context.get("weather", {})
        temp = w.get("air_temp_c", 32.0)
        wbgt = w.get("wbgt_sun_c", 28.0)

        if any(k in msg for k in ["heat", "worker", "safety", "work", "afternoon"]):
            if wbgt >= 29.0 or temp >= 38.0:
                return (
                    f"In {taluka}, outdoor WBGT is currently {wbgt:.1f}°C with air temperature at {temp:.1f}°C. "
                    f"Please avoid strenuous manual fieldwork between 11:30 AM and 3:30 PM. "
                    f"Ensure workers drink clean water every 20 minutes and rest under shade."
                )
            else:
                return (
                    f"Current field thermal conditions in {taluka} are within manageable limits (WBGT {wbgt:.1f}°C, Temp {temp:.1f}°C). "
                    f"Workers can perform normal scheduled tasks with standard hydration."
                )
        elif any(k in msg for k in ["crop", "stage", "risk", "damage", "health"]):
            crit = context.get("critical_temp_c", 35.0)
            if temp >= crit:
                return (
                    f"Your {crop} is currently at the {stage} stage. Air temperature ({temp:.1f}°C) has reached the thermal limit ({crit:.1f}°C). "
                    f"We recommend applying micro-sprinkler canopy misting or night-time drip pulse irrigation to protect flowering and bulb development."
                )
            else:
                return (
                    f"Your {crop} is at the {stage} stage and growing well under current {temp:.1f}°C temperatures, below the {crit:.1f}°C threshold. "
                    f"Maintain regular soil moisture checks."
                )
        elif any(k in msg for k in ["income", "money", "diversification", "earn"]):
            opps = context.get("income_opportunities", [])
            opp_names = ", ".join([o["title"] for o in opps]) if opps else "On-farm composting, Bund planting, or Backyard poultry"
            return (
                f"Based on your resources in {taluka}, suitable diversification opportunities include: {opp_names}. "
                f"These allow utilizing surplus crop residue or spare perimeter land with minimal cash outlay."
            )
        else:
            return (
                f"Hello {context.get('farmer_name')}. For your farm in {taluka}, your {crop} is currently at {stage} stage with temperature around {temp:.1f}°C. "
                f"You can ask me about heat safety, crop interventions, weather alerts, or extra income options."
            )
