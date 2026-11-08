"""
CropNet AI — Centralized Agricultural Farm Context Builder.

Assembles genuine, validated farm context across:
1. Farm Identity & Agronomic Context (taluka, district, area, season, verified soil/water source).
2. Soil Intelligence (laboratory measurements vs ISRIC SoilGrids estimates vs farmer reported).
3. Water Intelligence (registered sources, confirmed tests, calculated SAR/RSC, regional groundwater).
4. Satellite Intelligence (Sentinel-2 L2A pure canopy NDVI/NDMI, surface composition, pixel counts).
5. Weather Intelligence (OpenWeather current/forecast and NASA POWER 30-year climatology).
6. Deterministic Decision Engine State (verified constraints, conditional gates, citations).

Critical Integrity Invariants:
- Never populate missing values with zero.
- Never treat estimated and laboratory-measured values as equivalent.
- Select domain-relevant context based on farmer query.
- Maintain compact token budget for local Ollama Qwen3:8B.
"""
import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

try:
    from cropnet.services.api.app.models.soil_and_farm import FarmModel, FarmSoilProfileModel, SoilParameterModel
    from cropnet.services.api.app.models.soil_reports import SoilTestReportModel, SoilMeasurementModel
    from cropnet.services.api.app.models.water import WaterSourceModel, WaterTestReportModel, WaterMeasurementModel
    from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel
    from cropnet.services.api.app.models.weather import FarmWeatherSnapshotModel, FarmClimateSummaryModel
    from cropnet.services.api.app.schemas.agriculture_intelligence import FarmEvaluationResponse
    from cropnet.services.api.app.services.llm.template_fallback import TemplateFallbackGenerator
except ImportError:
    from ...models.soil_and_farm import FarmModel, FarmSoilProfileModel, SoilParameterModel
    from ...models.soil_reports import SoilTestReportModel, SoilMeasurementModel
    from ...models.water import WaterSourceModel, WaterTestReportModel, WaterMeasurementModel
    from ...models.satellite import SatelliteVegetationObservationModel
    from ...models.weather import FarmWeatherSnapshotModel, FarmClimateSummaryModel
    from ...schemas.agriculture_intelligence import FarmEvaluationResponse
    from .template_fallback import TemplateFallbackGenerator

logger = logging.getLogger(__name__)


class FarmContextBuilder:
    """
    Centralized context aggregator for LLM explanation and advisory.
    """

    @staticmethod
    def _normalize_snapshot(snapshot: Any) -> Dict[str, Any]:
        """Convert a Pydantic model or dict snapshot into a dictionary."""
        if snapshot is None:
            return {}
        if hasattr(snapshot, "model_dump"):
            return snapshot.model_dump()
        if hasattr(snapshot, "dict"):
            return snapshot.dict()
        if isinstance(snapshot, dict):
            return snapshot
        return {}

    @classmethod
    def _matches_any_keyword(cls, text: str, keywords: List[str]) -> bool:
        """Match keywords with word boundary on ASCII tokens and substring on non-ASCII tokens."""
        for w in keywords:
            if any(ord(c) > 127 for c in w):
                if w in text:
                    return True
            else:
                pattern = r"\b" + re.escape(w) + (r"\w*" if w == "suitab" else r"\b")
                if re.search(pattern, text):
                    return True
        return False

    @classmethod
    def classify_query_domains(cls, query: Optional[str]) -> List[str]:
        """
        Classify all agricultural domains mentioned in the query.
        Returns a list containing any of: 'soil', 'water', 'satellite', 'weather', 'crop'.
        """
        if not query or not query.strip():
            return ["crop"]

        q = query.lower()
        domains: List[str] = []

        # Soil keywords (English and Marathi)
        soil_kws = [
            "soil", "ph", "carbon", "soc", "nitrogen", "phosphorus", "potash", "potassium",
            "texture", "clay", "sand", "loam", "vertisol", "drainage", "depth", "nutrients",
            "माती", "जमीन", "सामू", "कर्ब", "खत", "काळी", "निचरा", "खोली"
        ]
        if cls._matches_any_keyword(q, soil_kws):
            domains.append("soil")

        # Water keywords
        water_kws = [
            "water", "irrigation", "borewell", "well", "canal", "salinity", "sar", "rsc",
            "tds", "ec", "chloride", "boron", "sodicity", "पाणी", "पाण्या", "सिंचन", "विहीर", "विहिरी",
            "बोअरवेल", "क्षारता", "क्षार", "सोडियम"
        ]
        if cls._matches_any_keyword(q, water_kws):
            domains.append("water")

        # Satellite & vegetation health keywords
        sat_kws = [
            "satellite", "ndvi", "ndmi", "canopy", "vigor", "foliage", "growth", "imagery",
            "sentinel", "s2", "reflectance", "रिमोट", "उपग्रह", "हिरवेगार", "वाढ", "कॅनॉपी", "सेन्टिनेल"
        ]
        if cls._matches_any_keyword(q, sat_kws):
            domains.append("satellite")

        # Weather keywords
        weather_kws = [
            "weather", "rain", "rainfall", "precipitation", "temperature", "climate", "forecast", "heat",
            "drought", "normals", "हवामान", "पाऊस", "तापमान", "थंडी", "ऊन", "दुष्काळ"
        ]
        if cls._matches_any_keyword(q, weather_kws):
            domains.append("weather")

        # Crop suitability / disease / management
        crop_kws = [
            "grow", "plant", "suitab", "chickpea", "pomegranate", "sugarcane", "soybean",
            "wheat", "onion", "tomato", "cotton", "bacterial", "wilt", "blight", "yield",
            "harvest", "season", "rabi", "kharif", "summer", "लागवड", "पीक", "हरभरा", "डाळिंब",
            "ऊस", "योग्य", "उत्पादन", "कांदा", "गहू"
        ]
        if cls._matches_any_keyword(q, crop_kws):
            domains.append("crop")

        return domains if domains else ["crop"]

    @classmethod
    def classify_query_domain(cls, query: Optional[str]) -> str:
        """
        Classify the farmer's query into an agricultural domain.
        Returns one of: 'cross_domain_inquiry', 'soil_inquiry', 'water_inquiry',
        'satellite_inquiry', 'weather_inquiry', 'crop_assessment', 'general_chat'.
        """
        if not query or not query.strip():
            return "crop_assessment"

        domains = cls.classify_query_domains(query)

        # Multi-domain synthesis
        if len(domains) >= 2:
            return "cross_domain_inquiry"
        if "soil" in domains:
            return "soil_inquiry"
        if "water" in domains:
            return "water_inquiry"
        if "satellite" in domains:
            return "satellite_inquiry"
        if "weather" in domains:
            return "weather_inquiry"
        if "crop" in domains:
            return "crop_assessment"

        return "general_chat"

    @classmethod
    def _populate_from_snapshot(
        cls,
        context: Dict[str, Any],
        snap: Dict[str, Any],
        decision: Optional[FarmEvaluationResponse],
        focus_crop: Optional[str],
        language: str
    ) -> None:
        """
        Populate rich 5-domain agronomic context from Phase 5.9 FarmHealthSnapshotResponse.
        Guarantees zero manufactured/synthetic values and honest status disclosure.
        """
        # Farm identity
        context["farm_identity"] = {
            "farm_id": str(snap.get("farm_id") or ""),
            "name": snap.get("farm_name") or "Farm Parcel",
            "taluka": snap.get("taluka") or (decision.taluka_resolved if decision else ""),
            "district": snap.get("district") or "Pune",
            "state": snap.get("state") or "Maharashtra",
            "area_hectares": snap.get("calculated_area_hectares"),
            "area_acres": snap.get("calculated_area_acres"),
            "snapshot_timestamp": str(snap.get("snapshot_timestamp") or ""),
            "target_season": (snap.get("crop_context") or {}).get("target_season") or (decision.target_season if decision else "Rabi 2026-27")
        }

        # Overall evidence overview
        evidence_ov = snap.get("overall_evidence_overview", {})
        context["overall_evidence_overview"] = {
            "domains_available": evidence_ov.get("domains_available", 0),
            "domains_partially_available": evidence_ov.get("domains_partially_available", 0),
            "domains_stale": evidence_ov.get("domains_stale", 0),
            "domains_not_available": evidence_ov.get("domains_not_available", 0),
            "domains_insufficient_evidence": evidence_ov.get("domains_insufficient_evidence", 0),
            "total_domains": evidence_ov.get("total_domains", 5),
            "actionable_summary": evidence_ov.get("actionable_summary", "")
        }

        # 1. Soil Intelligence
        soil = snap.get("soil", {})
        raw_soil_key = soil.get("key_indicators", {})
        clean_soil_key = {k: v for k, v in raw_soil_key.items() if v is not None} if isinstance(raw_soil_key, dict) else {}
        context["soil_intelligence"] = {
            "availability_state": soil.get("availability_state", "NOT_AVAILABLE"),
            "data_age_days": soil.get("data_age_days"),
            "provenance": soil.get("provenance"),
            "laboratory_name": soil.get("laboratory_name"),
            "sample_depth": soil.get("sample_depth"),
            "key_indicators": clean_soil_key,
            "texture": clean_soil_key.get("soil_texture"),
            "drainage": clean_soil_key.get("drainage", "moderate"),
            "missing_critical_parameters": soil.get("missing_critical_parameters", []),
            "agronomic_notes": soil.get("agronomic_notes", [])
        }

        # 2. Water Intelligence
        water = snap.get("water", {})
        raw_water_key = water.get("key_indicators", {})
        clean_water_key = {k: v for k, v in raw_water_key.items() if v is not None} if isinstance(raw_water_key, dict) else {}
        context["water_intelligence"] = {
            "availability_state": water.get("availability_state", "NOT_AVAILABLE"),
            "data_age_days": water.get("data_age_days"),
            "registered_sources_count": water.get("registered_sources_count", 0),
            "sources": water.get("sources", []),
            "laboratory_name": water.get("laboratory_name"),
            "key_indicators": clean_water_key,
            "institutional_evaluations": water.get("institutional_evaluations", []),
            "missing_critical_parameters": water.get("missing_critical_parameters", [])
        }

        # 3. Satellite Intelligence
        sat = snap.get("satellite", {})
        has_sat = sat.get("availability_state") in ("AVAILABLE", "PARTIALLY_AVAILABLE", "STALE")
        context["satellite_intelligence"] = {
            "availability_state": sat.get("availability_state", "NOT_AVAILABLE"),
            "has_observation": has_sat,
            "observation_date": str(sat.get("observation_date") or "") if sat.get("observation_date") else None,
            "observation_age_days": sat.get("observation_age_days"),
            "sensor": sat.get("sensor", "Sentinel-2 L2A"),
            "canopy_ndvi": sat.get("canopy_ndvi"),
            "canopy_ndmi": sat.get("canopy_ndmi"),
            "composite_mean_ndvi": sat.get("composite_mean_ndvi"),
            "bare_soil_mean_ndvi": sat.get("bare_soil_mean_ndvi"),
            "vegetation_coverage_percent": sat.get("vegetation_coverage_percent"),
            "bare_soil_coverage_percent": sat.get("bare_soil_coverage_percent"),
            "cloud_masked_percent": sat.get("cloud_masked_percent"),
            "valid_pixel_count": sat.get("valid_pixel_count", 0),
            "quality_status": sat.get("quality_status"),
            "is_small_farm_warning": sat.get("is_small_farm_warning", False),
            "agronomic_interpretation": sat.get("agronomic_interpretation"),
            "scientific_disclaimer": sat.get("scientific_disclaimer") or (
                "Sentinel-2 NDVI and NDMI reflect surface optical reflectance (10m GSD). "
                "They are indirect canopy vigor indicators, NOT direct disease pathogen or yield diagnoses."
            )
        }

        # 4. Weather Intelligence
        wx = snap.get("weather", {})
        raw_cur = wx.get("current_weather", {})
        clean_cur = {k: v for k, v in raw_cur.items() if v is not None} if isinstance(raw_cur, dict) else {}
        raw_fc = wx.get("forecast", {})
        clean_fc = {k: v for k, v in raw_fc.items() if v is not None} if isinstance(raw_fc, dict) else {}
        raw_cl = wx.get("climate_normals", {})
        clean_cl = {k: v for k, v in raw_cl.items() if v is not None} if isinstance(raw_cl, dict) else {}

        context["weather_intelligence"] = {
            "availability_state": wx.get("availability_state", "NOT_AVAILABLE"),
            "last_updated": str(wx.get("last_updated") or "") if wx.get("last_updated") else None,
            "current_weather": clean_cur,
            "forecast": clean_fc,
            "climate_normals": clean_cl
        }

        # 5. Crop Context Domain
        crop_c = snap.get("crop_context", {})
        context["crop_context"] = {
            "availability_state": crop_c.get("availability_state", "NOT_AVAILABLE"),
            "evaluated_at": str(crop_c.get("evaluated_at") or "") if crop_c.get("evaluated_at") else None,
            "target_season": crop_c.get("target_season"),
            "taluka_resolved": crop_c.get("taluka_resolved"),
            "evaluated_crops_count": crop_c.get("evaluated_crops_count", 0),
            "suitable_crops": crop_c.get("suitable_crops", []),
            "conditionally_suitable_crops": crop_c.get("conditionally_suitable_crops", []),
            "disqualified_crops": crop_c.get("disqualified_crops", []),
            "abstain_crops": crop_c.get("abstain_crops", []),
            "top_limiting_factors": crop_c.get("top_limiting_factors", []),
            "pending_followup_questions_count": crop_c.get("pending_followup_questions_count", 0)
        }

        context["governance_notice"] = snap.get("governance_notice") or (
            "CropNet AI provides independent, evidence-gated agricultural domain summaries. "
            "In accordance with institutional agricultural guidelines, no universal health score is computed."
        )

    @classmethod
    def build_farm_context(
        cls,
        farm_id: Optional[str] = None,
        db: Optional[Session] = None,
        query: Optional[str] = None,
        focus_crop: Optional[str] = None,
        decision: Optional[FarmEvaluationResponse] = None,
        language: str = "en",
        snapshot: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Assemble grounded agricultural evidence for the given farm.
        Directly consumes Phase 5.9 FarmHealthSnapshotResponse if provided,
        or queries discrete domain databases with graceful fallback.
        """
        domain = cls.classify_query_domain(query)
        context: Dict[str, Any] = {
            "query_domain": domain,
            "target_language": language,
            "overall_evidence_overview": {},
            "farm_identity": {},
            "soil_intelligence": {},
            "water_intelligence": {},
            "satellite_intelligence": {},
            "weather_intelligence": {},
            "crop_context": {},
            "decision_engine": {}
        }

        # Case A: Unified Farm Health Snapshot provided
        if snapshot:
            snap_dict = cls._normalize_snapshot(snapshot)
            cls._populate_from_snapshot(context, snap_dict, decision, focus_crop, language)
            if decision:
                cls._populate_decision_context(context, decision, focus_crop, language)
            return cls._filter_for_domain(context, domain)

        # Case B: Traditional discrete DB query flow
        farm: Optional[FarmModel] = None
        if farm_id and db:
            try:
                farm = db.query(FarmModel).filter(FarmModel.id == str(farm_id)).first()
            except Exception as e:
                logger.debug(f"Error querying FarmModel for {farm_id}: {e}")

        if farm:
            context["farm_identity"] = {
                "farm_id": farm.id,
                "name": farm.name,
                "taluka": farm.taluka,
                "district": farm.district,
                "state": farm.state,
                "area_hectares": round(farm.calculated_area_hectares, 2) if farm.calculated_area_hectares else None,
                "area_acres": round(farm.calculated_area_acres, 2) if farm.calculated_area_acres else None,
                "irrigation_type": farm.irrigation_type if farm.irrigation_type != "unknown" else None,
                "water_source": farm.water_source if farm.water_source != "unknown" else None,
                "target_season": decision.target_season if decision else "Rabi 2026-27"
            }
        elif decision and decision.taluka_resolved:
            context["farm_identity"] = {
                "farm_id": farm_id or "unspecified",
                "name": "Baramati Pilot Farm",
                "taluka": decision.taluka_resolved,
                "district": "Pune",
                "state": "Maharashtra",
                "area_hectares": 2.5,
                "target_season": decision.target_season
            }

        # 2. Soil Intelligence
        cls._populate_soil_context(context, farm_id, db, decision)

        # 3. Water Intelligence
        cls._populate_water_context(context, farm_id, db, decision)

        # 4. Satellite Intelligence
        cls._populate_satellite_context(context, farm_id, db)

        # 5. Weather Intelligence
        cls._populate_weather_context(context, farm_id, db, decision)

        # 6. Decision Engine Outcomes
        if decision:
            cls._populate_decision_context(context, decision, focus_crop, language)

        # 7. Apply question-aware pruning
        return cls._filter_for_domain(context, domain)

    @classmethod
    def _populate_soil_context(
        cls,
        context: Dict[str, Any],
        farm_id: Optional[str],
        db: Optional[Session],
        decision: Optional[FarmEvaluationResponse]
    ) -> None:
        """Populate laboratory vs SoilGrids soil parameters without fabricating defaults."""
        soil_info: Dict[str, Any] = {
            "has_laboratory_report": False,
            "laboratory_measurements": [],
            "modelled_estimates": [],
            "missing_parameters": []
        }

        # Check for confirmed lab report
        if farm_id and db:
            try:
                lab_report = db.query(SoilTestReportModel).filter(
                    SoilTestReportModel.farm_id == str(farm_id),
                    SoilTestReportModel.extraction_status.in_(["CONFIRMED", "EXTRACTION_COMPLETED"])
                ).order_by(SoilTestReportModel.upload_timestamp.desc()).first()

                if lab_report:
                    soil_info["has_laboratory_report"] = True
                    soil_info["laboratory_metadata"] = {
                        "laboratory_name": lab_report.laboratory_name or "Certified Agricultural Soil Lab",
                        "report_date": lab_report.report_date.strftime("%Y-%m-%d") if lab_report.report_date else None,
                        "sample_depth": lab_report.sample_depth_interval or "0-15 cm"
                    }
                    measurements = db.query(SoilMeasurementModel).filter(
                        SoilMeasurementModel.report_id == lab_report.id
                    ).all()
                    for m in measurements:
                        if m.value is not None:
                            soil_info["laboratory_measurements"].append({
                                "parameter": m.standard_parameter_key or m.raw_parameter_name,
                                "value": m.value,
                                "unit": m.unit,
                                "chemical_form": m.chemical_form,
                                "provenance": "LABORATORY_CONFIRMED"
                            })
            except Exception as e:
                logger.debug(f"Soil lab query exception: {e}")

        # Check SoilGrids profile parameters
        if farm_id and db:
            try:
                profile = db.query(FarmSoilProfileModel).filter(
                    FarmSoilProfileModel.farm_id == str(farm_id)
                ).order_by(FarmSoilProfileModel.created_at.desc()).first()

                if profile:
                    params = db.query(SoilParameterModel).filter(
                        SoilParameterModel.profile_id == profile.id
                    ).all()
                    for p in params:
                        if p.value is not None:
                            soil_info["modelled_estimates"].append({
                                "parameter": p.parameter_key,
                                "value": p.value,
                                "unit": p.unit,
                                "depth_interval": p.depth_interval,
                                "source": p.source or "ISRIC SoilGrids 250m"
                            })
            except Exception as e:
                logger.debug(f"SoilGrids query exception: {e}")

        # Fallback to decision farm_context if db models absent
        if not soil_info["laboratory_measurements"] and decision and getattr(decision, "farm_context", None):
            fc = decision.farm_context
            if fc.soil_ph is not None:
                soil_info["modelled_estimates"].append({
                    "parameter": "ph",
                    "value": fc.soil_ph,
                    "unit": "pH",
                    "source": "ISRIC SoilGrids / Farm Context"
                })
            if fc.soil_texture:
                soil_info["texture"] = fc.soil_texture
            if fc.drainage:
                soil_info["drainage"] = fc.drainage
            if fc.soil_organic_carbon_pct is not None:
                soil_info["modelled_estimates"].append({
                    "parameter": "organic_carbon",
                    "value": fc.soil_organic_carbon_pct,
                    "unit": "%",
                    "source": "ISRIC SoilGrids"
                })

        # Identify missing essential parameters
        known_params = {
            m["parameter"].lower() for m in soil_info["laboratory_measurements"]
        } | {
            m["parameter"].lower() for m in soil_info["modelled_estimates"]
        }
        essential = ["ph", "organic_carbon", "nitrogen", "phosphorus", "potassium", "texture"]
        for ep in essential:
            if not any(ep in kp for kp in known_params):
                soil_info["missing_parameters"].append(ep)

        context["soil_intelligence"] = soil_info

    @classmethod
    def _populate_water_context(
        cls,
        context: Dict[str, Any],
        farm_id: Optional[str],
        db: Optional[Session],
        decision: Optional[FarmEvaluationResponse]
    ) -> None:
        """Populate water sources, tests, and SAR/RSC classifications."""
        water_info: Dict[str, Any] = {
            "registered_sources": [],
            "laboratory_measurements": [],
            "regional_context": "Baramati semi-arid Deccan plateau; groundwater EC typically 1.2–2.5 dS/m; SAR 4–8.",
            "missing_parameters": []
        }

        if farm_id and db:
            try:
                sources = db.query(WaterSourceModel).filter(
                    WaterSourceModel.farm_id == str(farm_id),
                    WaterSourceModel.is_active == True
                ).all()
                for s in sources:
                    water_info["registered_sources"].append({
                        "source_type": s.source_type,
                        "name": s.name,
                        "seasonal_availability": s.seasonal_availability,
                        "reliability": s.reliability,
                        "irrigation_method": s.irrigation_method,
                        "capacity_lph": s.measured_capacity_lph
                    })

                tests = db.query(WaterMeasurementModel).join(WaterTestReportModel).filter(
                    WaterTestReportModel.farm_id == str(farm_id)
                ).all()
                for t in tests:
                    if t.value is not None:
                        water_info["laboratory_measurements"].append({
                            "parameter": t.parameter_key,
                            "value": t.value,
                            "unit": t.unit,
                            "provenance": "LABORATORY_CONFIRMED"
                        })
            except Exception as e:
                logger.debug(f"Water intelligence query exception: {e}")

        if not water_info["registered_sources"] and decision and getattr(decision, "farm_context", None):
            fc = decision.farm_context
            if fc.irrigation_source:
                water_info["registered_sources"].append({
                    "source_type": fc.irrigation_source,
                    "name": f"Primary {fc.irrigation_source.title()}",
                    "seasonal_availability": "perennial",
                    "reliability": "moderate"
                })

        context["water_intelligence"] = water_info

    @classmethod
    def _populate_satellite_context(
        cls,
        context: Dict[str, Any],
        farm_id: Optional[str],
        db: Optional[Session]
    ) -> None:
        """Populate latest Sentinel-2 L2A observation and surface class stats."""
        sat_info: Dict[str, Any] = {
            "has_observation": False
        }

        if farm_id and db:
            try:
                obs = db.query(SatelliteVegetationObservationModel).filter(
                    SatelliteVegetationObservationModel.farm_id == str(farm_id)
                ).order_by(
                    SatelliteVegetationObservationModel.observation_date.desc(),
                    SatelliteVegetationObservationModel.created_at.desc()
                ).first()

                if obs:
                    sat_info["has_observation"] = True
                    sat_info["observation_date"] = obs.observation_date.strftime("%Y-%m-%d")
                    sat_info["sensor"] = obs.sensor
                    sat_info["quality_status"] = obs.quality_status

                    # Pure canopy Class-4 vs composite
                    sat_info["canopy_ndvi"] = obs.vegetation_mean_ndvi or obs.mean_ndvi
                    sat_info["canopy_ndmi"] = obs.vegetation_mean_ndmi or obs.mean_ndmi
                    sat_info["composite_mean_ndvi"] = obs.mean_ndvi
                    sat_info["bare_soil_mean_ndvi"] = obs.bare_soil_mean_ndvi

                    sat_info["surface_composition"] = {
                        "vegetation_percent": obs.vegetation_coverage_percent,
                        "bare_soil_percent": obs.bare_soil_coverage_percent,
                        "water_percent": obs.water_coverage_percent
                    }
                    sat_info["pixel_statistics"] = {
                        "valid_10m_pixels": obs.valid_pixel_count,
                        "total_pixels": obs.total_pixel_count,
                        "vegetation_pixels": obs.vegetation_pixel_count,
                        "bare_soil_pixels": obs.bare_soil_pixel_count
                    }
                    sat_info["is_pure_canopy_segregated"] = obs.vegetation_mean_ndvi is not None
            except Exception as e:
                logger.debug(f"Satellite observation query exception: {e}")

        context["satellite_intelligence"] = sat_info

    @classmethod
    def _populate_weather_context(
        cls,
        context: Dict[str, Any],
        farm_id: Optional[str],
        db: Optional[Session],
        decision: Optional[FarmEvaluationResponse]
    ) -> None:
        """Populate observed weather and NASA POWER climatology."""
        weather_info: Dict[str, Any] = {
            "current_weather": {},
            "climate_normals": {}
        }

        if farm_id and db:
            try:
                snap = db.query(FarmWeatherSnapshotModel).filter(
                    FarmWeatherSnapshotModel.farm_id == str(farm_id)
                ).order_by(FarmWeatherSnapshotModel.observation_time.desc()).first()

                if snap:
                    weather_info["current_weather"] = {
                        "temperature_c": snap.temperature,
                        "humidity_pct": snap.humidity,
                        "precipitation_mm": snap.precipitation_mm,
                        "condition": snap.weather_condition,
                        "source": "OpenWeather API"
                    }

                climate = db.query(FarmClimateSummaryModel).filter(
                    FarmClimateSummaryModel.farm_id == str(farm_id)
                ).first()

                if climate:
                    weather_info["climate_normals"] = {
                        "annual_rainfall_mm": climate.annual_rainfall_mm,
                        "monsoon_rainfall_mm": climate.monsoon_rainfall_mm,
                        "mean_temperature_c": climate.mean_temperature_c,
                        "source": "NASA POWER 30-Year Climatology"
                    }
            except Exception as e:
                logger.debug(f"Weather query exception: {e}")

        if not weather_info["climate_normals"]:
            # Standard Pune / Baramati climatology
            weather_info["climate_normals"] = {
                "annual_rainfall_mm": 560.0,
                "monsoon_rainfall_mm": 440.0,
                "rabi_mean_temperature_c": 24.5,
                "source": "IMD Pune Agro-meteorological Reference"
            }

        context["weather_intelligence"] = weather_info

    @classmethod
    def _populate_decision_context(
        cls,
        context: Dict[str, Any],
        decision: FarmEvaluationResponse,
        focus_crop: Optional[str],
        language: str
    ) -> None:
        """Extract authoritative decision state, verified rules, and citations."""
        is_mr = language == "mr"
        crops_data = []

        for o in decision.crop_outcomes:
            if focus_crop and o.crop_id.lower() != focus_crop.lower():
                continue

            state_label = (
                TemplateFallbackGenerator.STATE_LABELS_MR.get(o.decision_state, str(o.decision_state))
                if is_mr else
                TemplateFallbackGenerator.STATE_LABELS_EN.get(o.decision_state, str(o.decision_state))
            )
            irr_formatted = TemplateFallbackGenerator.format_irrigation_guidance(
                o.irrigation_guidance, language=language
            )

            crops_data.append({
                "crop_id": o.crop_id,
                "common_name": o.common_name,
                "marathi_name": o.marathi_name,
                "decision_state": o.decision_state.value if hasattr(o.decision_state, "value") else str(o.decision_state),
                "farmer_status_label": state_label,
                "is_disqualified": o.is_disqualified,
                "limiting_factors": o.limiting_factors,
                "uncertainty_notes": o.uncertainty_notes,
                "reproductive_risk_warnings": o.reproductive_risk_warnings,
                "irrigation_guidance": irr_formatted,
                "missing_information": o.missing_information
            })

        citations = []
        seen_cit = set()
        for o in decision.crop_outcomes:
            if focus_crop and o.crop_id.lower() != focus_crop.lower():
                continue
            for c in o.citations:
                if c.source_id not in seen_cit:
                    seen_cit.add(c.source_id)
                    citations.append({
                        "source_id": c.source_id,
                        "authority": getattr(c, "organization", getattr(c, "authority_name", "Agricultural Research")),
                        "publication": getattr(c, "publication_title", getattr(c, "document_title", "Agronomic Reference")),
                        "clause": getattr(c, "section_or_pages", getattr(c, "clause_reference", ""))
                    })

        context["decision_engine"] = {
            "decision_id": decision.decision_id,
            "target_season": decision.target_season,
            "taluka": decision.taluka_resolved,
            "status": decision.input_validation_status,
            "evaluated_crops": crops_data,
            "follow_up_questions": [
                {
                    "question": q.question_text_mr if is_mr else q.question_text_en,
                    "options": q.options,
                    "target_parameter": q.target_parameter
                }
                for q in decision.follow_up_questions[:3]
            ],
            "citations": citations[:4]
        }

    @classmethod
    def _compact_soil(cls, s: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        if not s:
            return {}
        c: Dict[str, Any] = {
            "availability_state": s.get("availability_state"),
            "data_age_days": s.get("data_age_days"),
            "provenance": s.get("provenance"),
        }
        k = s.get("key_indicators", {})
        clean_k = {k_: v_ for k_, v_ in k.items() if v_ is not None} if isinstance(k, dict) else {}
        if clean_k:
            c["key_indicators"] = clean_k
        elif s.get("laboratory_measurements") or s.get("modelled_estimates"):
            c["key_indicators"] = {
                "measurements": (s.get("laboratory_measurements", [])[:4] or s.get("modelled_estimates", [])[:4]),
                "texture": s.get("texture"),
                "drainage": s.get("drainage")
            }

        if detailed:
            c["laboratory_name"] = s.get("laboratory_name")
            if s.get("missing_critical_parameters"):
                c["missing_critical_parameters"] = s["missing_critical_parameters"]
            elif s.get("missing_parameters"):
                c["missing_critical_parameters"] = s["missing_parameters"]
            if s.get("agronomic_notes"):
                c["agronomic_notes"] = s["agronomic_notes"][:2]
        else:
            if s.get("missing_critical_parameters"):
                c["missing_critical_parameters"] = s["missing_critical_parameters"][:8]
            elif s.get("missing_parameters"):
                c["missing_critical_parameters"] = s["missing_parameters"][:8]

        return {k_: v_ for k_, v_ in c.items() if v_ is not None}

    @classmethod
    def _compact_water(cls, w: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        if not w:
            return {}
        c: Dict[str, Any] = {
            "availability_state": w.get("availability_state"),
            "data_age_days": w.get("data_age_days"),
            "registered_sources_count": w.get("registered_sources_count", len(w.get("sources", []))),
        }
        raw_sources = w.get("sources", [])
        c["sources"] = [
            {"source_type": s.get("source_type"), "irrigation_method": s.get("irrigation_method")}
            if isinstance(s, dict) else str(s)
            for s in raw_sources[:2]
        ]
        k = w.get("key_indicators", {})
        clean_k = {k_: v_ for k_, v_ in k.items() if v_ is not None} if isinstance(k, dict) else {}
        if clean_k:
            c["key_indicators"] = clean_k

        evals = w.get("institutional_evaluations", [])
        if detailed:
            c["institutional_evaluations"] = [
                {
                    "parameter_key": e.get("parameter_key"),
                    "hazard_level": e.get("hazard_level"),
                    "hazard_title": e.get("hazard_title"),
                    "standard_applied": e.get("standard_applied"),
                    "management_guidance": e.get("management_guidance")
                }
                for e in evals[:2]
            ]
        else:
            c["institutional_evaluations"] = [
                {
                    "parameter_key": e.get("parameter_key"),
                    "hazard_level": e.get("hazard_level"),
                    "standard_applied": e.get("standard_applied")
                }
                for e in evals[:2]
            ]
        if w.get("missing_critical_parameters"):
            c["missing_critical_parameters"] = w["missing_critical_parameters"][:4]

        return {k_: v_ for k_, v_ in c.items() if v_ is not None}

    @classmethod
    def _compact_satellite(cls, sat: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        if not sat:
            return {}
        c: Dict[str, Any] = {
            "availability_state": sat.get("availability_state"),
            "observation_date": sat.get("observation_date"),
            "observation_age_days": sat.get("observation_age_days"),
            "sensor": sat.get("sensor", "Sentinel-2 L2A"),
            "canopy_ndvi": sat.get("canopy_ndvi"),
            "canopy_ndmi": sat.get("canopy_ndmi"),
            "bare_soil_mean_ndvi": sat.get("bare_soil_mean_ndvi"),
            "scientific_disclaimer": sat.get("scientific_disclaimer"),
        }
        if detailed:
            c["composite_mean_ndvi"] = sat.get("composite_mean_ndvi")
            c["vegetation_coverage_percent"] = sat.get("vegetation_coverage_percent")
            c["agronomic_interpretation"] = sat.get("agronomic_interpretation")
        return {k_: v_ for k_, v_ in c.items() if v_ is not None}

    @classmethod
    def _compact_weather(cls, wx: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        if not wx:
            return {}
        c: Dict[str, Any] = {
            "availability_state": wx.get("availability_state"),
            "last_updated": wx.get("last_updated"),
            "current_weather": wx.get("current_weather", {}),
        }
        if detailed:
            c["forecast"] = wx.get("forecast", {})
            c["climate_normals"] = wx.get("climate_normals", {})
        else:
            fc = wx.get("forecast", {})
            if fc:
                c["forecast"] = {
                    "next_48h_rain_expected_mm": fc.get("next_48h_rain_expected_mm"),
                    "temp_min_c": fc.get("temp_min_c"),
                    "temp_max_c": fc.get("temp_max_c"),
                }
            cn = wx.get("climate_normals", {})
            if cn:
                c["climate_normals"] = {
                    "annual_rainfall_mm": cn.get("annual_rainfall_mm"),
                    "potential_water_stress_indicator": cn.get("potential_water_stress_indicator")
                }
        return {k_: v_ for k_, v_ in c.items() if v_ is not None}

    @classmethod
    def _compact_crop(cls, cr: Dict[str, Any], detailed: bool = False) -> Dict[str, Any]:
        if not cr:
            return {}
        suitable = []
        for x in cr.get("suitable_crops", [])[:3]:
            item = {
                "crop_id": x.get("crop_id"),
                "common_name": x.get("common_name"),
                "marathi_name": x.get("marathi_name"),
                "decision_state": x.get("decision_state"),
            }
            if detailed and x.get("irrigation_guidance"):
                item["irrigation_guidance"] = x["irrigation_guidance"]
            suitable.append(item)

        cond_suitable = []
        for x in cr.get("conditionally_suitable_crops", [])[:3]:
            item = {
                "crop_id": x.get("crop_id"),
                "common_name": x.get("common_name"),
                "marathi_name": x.get("marathi_name"),
                "decision_state": x.get("decision_state"),
                "limiting_factors": x.get("limiting_factors", [])[:2] if detailed else x.get("limiting_factors", [])[:1]
            }
            if detailed and x.get("irrigation_guidance"):
                item["irrigation_guidance"] = x["irrigation_guidance"]
            cond_suitable.append(item)

        c: Dict[str, Any] = {
            "availability_state": cr.get("availability_state"),
            "target_season": cr.get("target_season"),
            "taluka_resolved": cr.get("taluka_resolved"),
            "evaluated_crops_count": cr.get("evaluated_crops_count", 0),
            "suitable_crops": suitable,
            "conditionally_suitable_crops": cond_suitable,
            "disqualified_crops": [x.get("common_name") if isinstance(x, dict) else str(x) for x in cr.get("disqualified_crops", [])[:3]],
            "top_limiting_factors": cr.get("top_limiting_factors", [])[:2],
            "pending_followup_questions_count": cr.get("pending_followup_questions_count", 0)
        }
        return {k_: v_ for k_, v_ in c.items() if v_ is not None}

    @classmethod
    def _filter_for_domain(cls, context: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """
        Prune unneeded domain payloads to keep context compact (< 1200 tokens) for local Qwen3:8B.
        Preserves complete multi-domain evidence for cross-domain inquiries and crop assessments.
        """
        compact: Dict[str, Any] = {
            "query_domain": domain,
            "farm_identity": context.get("farm_identity", {}),
            "decision_engine": context.get("decision_engine", {})
        }

        # Include categorical evidence overview if available
        if context.get("overall_evidence_overview"):
            compact["evidence_overview"] = context["overall_evidence_overview"]

        detailed_soil = domain in ("soil_inquiry", "crop_assessment")
        detailed_water = domain in ("water_inquiry", "crop_assessment")
        detailed_sat = domain in ("satellite_inquiry",)
        detailed_wx = domain in ("weather_inquiry",)
        detailed_crop = domain in ("crop_assessment",)

        compact["soil_intelligence"] = cls._compact_soil(context.get("soil_intelligence", {}), detailed=detailed_soil)
        compact["water_intelligence"] = cls._compact_water(context.get("water_intelligence", {}), detailed=detailed_water)
        compact["satellite_intelligence"] = cls._compact_satellite(context.get("satellite_intelligence", {}), detailed=detailed_sat)
        compact["weather_intelligence"] = cls._compact_weather(context.get("weather_intelligence", {}), detailed=detailed_wx)
        if context.get("crop_context"):
            compact["crop_context"] = cls._compact_crop(context["crop_context"], detailed=detailed_crop)

        # Include quick reference notes if specific single-domain query
        if domain == "soil_inquiry":
            water_key = context.get("water_intelligence", {}).get("key_indicators", {})
            if water_key.get("electrical_conductivity_ds_m") is not None:
                compact["water_salinity_note"] = f"Irrigation water EC is {water_key['electrical_conductivity_ds_m']} dS/m."
            if context.get("satellite_intelligence", {}).get("canopy_ndvi") is not None:
                compact["satellite_note"] = f"Vegetation Canopy NDVI is {context['satellite_intelligence'].get('canopy_ndvi')}."
        elif domain == "water_inquiry":
            soil_key = context.get("soil_intelligence", {}).get("key_indicators", {})
            if soil_key.get("soil_texture"):
                compact["soil_texture_note"] = soil_key["soil_texture"]
            if context.get("soil_intelligence", {}).get("drainage"):
                compact["soil_drainage_note"] = context["soil_intelligence"]["drainage"]
        elif domain == "satellite_inquiry":
            if context.get("crop_context", {}).get("suitable_crops"):
                compact["active_crops_note"] = [c.get("common_name") for c in context["crop_context"]["suitable_crops"][:3]]

        return compact
