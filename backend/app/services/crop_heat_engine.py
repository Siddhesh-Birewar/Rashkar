import uuid
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.timezone import now_utc, now_ist
from backend.app.services.weather_service import WeatherService
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.db.models.crop_knowledge import (
    CanonicalCropMasterModel,
    AgronomicThresholdRegistryModel,
    AgronomicAdvisoryCatalogueModel
)
from backend.app.db.models.risk import CropHeatAssessmentLogModel
from backend.app.services.crop_stage_service import CropStageService
from backend.app.schemas.crop_heat import (
    CropHeatAssessmentRequest,
    CropHeatAssessmentResponse,
    CropHeatIntervention
)

class CropHeatEngine:
    @staticmethod
    def assess_crop_heat_risk(
        db: Session,
        request: CropHeatAssessmentRequest
    ) -> CropHeatAssessmentResponse:
        assessment_id = f"cha_{uuid.uuid4().hex[:12]}"
        now_dt_utc = now_utc()
        now_dt_ist = now_ist()

        # 1. Lookup farm and crop cycle
        farm = db.query(FarmModel).filter(FarmModel.farm_id == request.farm_id).first()
        if not farm:
            raise ValueError(f"Farm with id '{request.farm_id}' not found.")

        # Find active crop cycle
        query = db.query(CropCycleModel).join(FarmPlotModel).filter(
            FarmPlotModel.farm_id == request.farm_id,
            CropCycleModel.is_active == True
        )
        if request.plot_id:
            query = query.filter(CropCycleModel.plot_id == request.plot_id)
        crop_cycle = query.first()

        if not crop_cycle:
            raise ValueError(f"No active crop cycle found for farm '{request.farm_id}'.")

        crop_code = crop_cycle.crop_code.lower()
        canonical_crop = db.query(CanonicalCropMasterModel).filter(
            CanonicalCropMasterModel.crop_code == crop_code
        ).first()
        crop_name = canonical_crop.common_name_en if canonical_crop else crop_code.capitalize()

        # 2. Determine growth stage
        stage_info = CropStageService.estimate_crop_stage(
            db=db,
            crop_code=crop_code,
            sowing_date=crop_cycle.sowing_date,
            farmer_confirmed_stage=crop_cycle.current_stage_code
        )
        stage_code = stage_info["stage_code"]

        # 3. Lookup scientific thermal thresholds from DB registry
        # A. Daytime Tmax threshold
        tmax_thresh_record = db.query(AgronomicThresholdRegistryModel).filter(
            AgronomicThresholdRegistryModel.crop_code == crop_code,
            AgronomicThresholdRegistryModel.growth_stage == stage_code,
            AgronomicThresholdRegistryModel.environmental_variable == "tmax_c"
        ).first()

        if not tmax_thresh_record:
            # Fallback to general crop tmax threshold
            tmax_thresh_record = db.query(AgronomicThresholdRegistryModel).filter(
                AgronomicThresholdRegistryModel.crop_code == crop_code,
                AgronomicThresholdRegistryModel.environmental_variable == "tmax_c"
            ).first()

        critical_tmax = tmax_thresh_record.critical_threshold if tmax_thresh_record else 38.0
        citation = (
            f"{tmax_thresh_record.source_institution} ({tmax_thresh_record.publication_citation})"
            if tmax_thresh_record else "ICAR-SAU Agronomic Guidelines"
        )
        physio_impact = (
            tmax_thresh_record.physiological_impact
            if tmax_thresh_record else "Thermal stress during critical phenological phase."
        )

        # B. Nighttime Tmin threshold (warm night respiration)
        tmin_thresh_record = db.query(AgronomicThresholdRegistryModel).filter(
            AgronomicThresholdRegistryModel.crop_code == crop_code,
            AgronomicThresholdRegistryModel.environmental_variable == "tmin_c"
        ).first()
        critical_tmin = tmin_thresh_record.critical_threshold if tmin_thresh_record else 24.0

        # 4. Forecast values (use overrides or live weather service for farm coordinates)
        if request.forecast_tmax_c is not None:
            tmax_forecast = request.forecast_tmax_c
            tmin_forecast = request.forecast_tmin_c if request.forecast_tmin_c is not None else 24.0
        else:
            fc = WeatherService.get_hourly_forecast(farm.latitude, farm.longitude, horizon_hours=6)
            pts = fc.get("hourly_points", [])
            if pts:
                tmax_forecast = max(p.get("air_temp_c", 33.0) for p in pts)
                tmin_forecast = min(p.get("air_temp_c", 23.0) for p in pts)
            else:
                tmax_forecast = 34.0
                tmin_forecast = 23.0

        # Evaluate Daytime Heat Stress Level
        tmax_diff = tmax_forecast - critical_tmax
        if tmax_diff >= 2.0:
            daytime_stress = "critical"
        elif tmax_diff >= 0.0:
            daytime_stress = "high"
        elif tmax_diff >= -2.0:
            daytime_stress = "moderate"
        else:
            daytime_stress = "low"

        # Evaluate Warm Night Respiration Hazard
        warm_night = (tmin_forecast >= critical_tmin)

        # Overall risk level
        if daytime_stress in ["critical", "high"] or (daytime_stress == "moderate" and warm_night):
            overall_risk = "high" if daytime_stress != "critical" else "critical"
        elif daytime_stress == "moderate" or warm_night:
            overall_risk = "moderate"
        else:
            overall_risk = "low"

        # 5. Fetch actionable interventions from advisory catalogue
        interventions: List[CropHeatIntervention] = []
        advisories = db.query(AgronomicAdvisoryCatalogueModel).filter(
            AgronomicAdvisoryCatalogueModel.crop_code == crop_code,
            AgronomicAdvisoryCatalogueModel.risk_dimension == "crop_heat"
        ).all()

        for adv in advisories:
            interventions.append(CropHeatIntervention(
                intervention_id=adv.action_id,
                title_en=adv.title_en,
                title_mr=adv.title_mr,
                description_en=adv.description_en,
                description_mr=adv.description_mr,
                evidence_citation=adv.evidence_citation
            ))

        # Default standard mitigation if specific crop advisory is empty
        if not interventions:
            interventions.append(CropHeatIntervention(
                intervention_id="INTERV_MICRO_IRRIG",
                title_en="Evening Micro-Irrigation for Canopy Cooling",
                title_mr="पिकाच्या थंडाव्यासाठी संध्याकाळी सूक्ष्म सिंचन",
                description_en="Apply light sprinkler or drip irrigation during late evening hours to cool the root-zone and canopy microclimate by 2-3°C.",
                description_mr="मुळांभोवतालचे व पिकाचे तापमान २-३ अंशांनी कमी करण्यासाठी संध्याकाळी हलके पाणी द्यावे.",
                evidence_citation="ICAR-CRIDA Climate Resilient Agriculture Compendium"
            ))

        # 6. Audit logging
        audit_saved = False
        try:
            audit_entry = CropHeatAssessmentLogModel(
                assessment_id=assessment_id,
                farm_id=request.farm_id,
                crop_code=crop_code,
                stage_code=stage_code,
                generated_at_utc=now_dt_utc,
                max_forecast_temp_c=tmax_forecast,
                critical_threshold_c=critical_tmax,
                exceedance_hours=4 if daytime_stress in ["high", "critical"] else 0,
                warm_night_flag=warm_night,
                risk_level=overall_risk,
                evidence_citation=citation
            )
            db.add(audit_entry)
            db.commit()
            audit_saved = True
        except Exception:
            db.rollback()
            audit_saved = False

        return CropHeatAssessmentResponse(
            assessment_id=assessment_id,
            farm_id=request.farm_id,
            crop_code=crop_code,
            crop_common_name=crop_name,
            growth_stage_code=stage_code,
            growth_stage_name_en=stage_info["stage_name_en"],
            growth_stage_name_mr=stage_info["stage_name_mr"],
            generated_at_ist=now_dt_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            tmax_forecast_c=tmax_forecast,
            tmin_forecast_c=tmin_forecast,
            critical_tmax_threshold_c=critical_tmax,
            critical_tmin_threshold_c=critical_tmin,
            daytime_heat_stress_level=daytime_stress,
            warm_night_respiration_hazard=warm_night,
            overall_crop_heat_risk=overall_risk,
            physiological_mechanism=physio_impact,
            evidence_citation=citation,
            recommended_interventions=interventions,
            audit_logged=audit_saved
        )
