from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from backend.app.schemas.dashboard import (
    IssueSeverity,
    DashboardIssue,
    DashboardSummaryResponse
)
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel
from backend.app.services.weather_service import WeatherService
from backend.app.services.wbgt_solver import calculate_wbgt
from backend.app.services.crop_heat_engine import CropHeatEngine
from backend.app.db.models.crop_knowledge import CropStageReferenceModel

class DashboardIssueService:
    @staticmethod
    def get_farm_dashboard_issues(db: Session, farm_id: str) -> DashboardSummaryResponse:
        farm = db.query(FarmModel).filter(FarmModel.farm_id == farm_id).first()
        farm_name = farm.farm_name if farm else "My Farm"
        lat = farm.latitude if farm else 20.08
        lon = farm.longitude if farm else 74.08
        
        issues: List[DashboardIssue] = []

        # 1. Fetch current weather and compute worker heat risk
        t_air = 32.0
        try:
            weather = WeatherService.get_current_weather_and_forecast(lat=lat, lon=lon)
            curr = weather.get("current", {})
            t_air = float(curr.get("temperature_c", 32.0))
            rh = float(curr.get("humidity_pct", 50.0))
            wind = float(curr.get("wind_speed_ms", 1.5))
            solar = float(curr.get("solar_radiation_wm2", 650.0))

            wbgt_res = calculate_wbgt(
                temp_c=t_air, rh_pct=rh, wind_speed_ms=wind, solar_irradiance_wm2=solar,
                in_sun=True
            )
            wbgt_val = wbgt_res.get("wbgt_estimated_c", 28.0)

            if wbgt_val >= 30.5 or t_air >= 41.0:
                issues.append(DashboardIssue(
                    issue_id=f"worker_heat_{farm_id}_urgent",
                    domain="worker_heat",
                    severity=IssueSeverity.URGENT_ATTENTION,
                    title="Extreme Heat Danger for Workers",
                    summary=f"Current outdoor WBGT has reached {wbgt_val:.1f}°C (Air temp {t_air:.1f}°C). ACGIH safety threshold exceeded.",
                    recommended_action="Cease strenuous manual fieldwork between 11:30 AM and 3:30 PM. Mandate 45 min/hr rest under shade.",
                    action_target_route="/heat-safety",
                    action_button_label="Open Heat Safety",
                    evidence={"wbgt_c": round(wbgt_val, 1), "air_temp_c": round(t_air, 1)}
                ))
            elif wbgt_val >= 28.0 or t_air >= 36.0:
                issues.append(DashboardIssue(
                    issue_id=f"worker_heat_{farm_id}_warn",
                    domain="worker_heat",
                    severity=IssueSeverity.NEEDS_ATTENTION,
                    title="Moderate Worker Heat Alert",
                    summary=f"Field WBGT is elevated at {wbgt_val:.1f}°C. Heavy agricultural labor requires frequent hydration pauses.",
                    recommended_action="Ensure 250ml water intake every 20 minutes and schedule heavy tasks for early morning.",
                    action_target_route="/heat-safety",
                    action_button_label="View Hydration Schedule",
                    evidence={"wbgt_c": round(wbgt_val, 1), "air_temp_c": round(t_air, 1)}
                ))
        except Exception:
            pass

        # 2. Check Crop Cycles for Crop Heat Risk & Season Expiry
        if farm and farm.plots:
            for plot in farm.plots:
                for cycle in plot.crop_cycles:
                    if cycle.is_active:
                        # Check season expiry
                        sowing = cycle.sowing_date
                        if sowing:
                            try:
                                if hasattr(sowing, "strftime"):
                                    sowing_dt = datetime.combine(sowing, datetime.min.time())
                                else:
                                    sowing_dt = datetime.strptime(str(sowing), "%Y-%m-%d")
                                days_after_sowing = (datetime.now() - sowing_dt).days
                                if days_after_sowing > 150:
                                    crop_display = cycle.crop_code.capitalize()
                                    issues.append(DashboardIssue(
                                        issue_id=f"cycle_expired_{cycle.cycle_id}",
                                        domain="season_integrity",
                                        severity=IssueSeverity.NEEDS_ATTENTION,
                                        title=f"Crop Season Completed: {crop_display}",
                                        summary=f"{crop_display} is at {days_after_sowing} DAS, exceeding typical lifecycle. Heat risk is suppressed.",
                                        recommended_action="Confirm final harvest to update your farm records and refresh soil status.",
                                        action_target_route="/my-crop",
                                        action_button_label="Confirm Harvest",
                                        evidence={"days_after_sowing": days_after_sowing, "crop_name": crop_display}
                                    ))
                                    continue
                            except Exception:
                                pass

                        # Check crop heat risk for active cycle
                        crop_code = cycle.crop_code.lower().strip()
                        stage_ref = (
                            db.query(CropStageReferenceModel)
                            .filter(
                                CropStageReferenceModel.crop_code == crop_code,
                                CropStageReferenceModel.stage_code == cycle.current_stage_code
                            )
                            .first()
                        )
                        critical_temp = stage_ref.critical_temp_c if stage_ref else 35.0
                        
                        if t_air >= critical_temp:
                            crop_display = cycle.crop_code.capitalize()
                            issues.append(DashboardIssue(
                                issue_id=f"crop_heat_{cycle.cycle_id}",
                                domain="crop_heat",
                                severity=IssueSeverity.URGENT_ATTENTION if (t_air - critical_temp) >= 2.0 else IssueSeverity.NEEDS_ATTENTION,
                                title=f"Heat Exceedance on {crop_display}",
                                summary=f"Air temperature ({t_air:.1f}°C) exceeds thermal limit ({critical_temp:.1f}°C) for {cycle.current_stage_code or 'current stage'}.",
                                recommended_action="Apply micro-sprinkler canopy cooling or light evening drip irrigation to lower surface temperature.",
                                action_target_route="/my-crop",
                                action_button_label="View Crop Interventions",
                                evidence={"air_temp_c": round(t_air, 1), "critical_temp_c": critical_temp, "crop": crop_display}
                            ))

        # 3. Sort issues by severity priority
        severity_order = {
            IssueSeverity.URGENT_ATTENTION: 0,
            IssueSeverity.NEEDS_ATTENTION: 1,
            IssueSeverity.KEEP_AN_EYE_ON: 2,
            IssueSeverity.INFORMATION: 3
        }
        issues.sort(key=lambda x: severity_order.get(x.severity, 4))

        has_urgent = any(i.severity == IssueSeverity.URGENT_ATTENTION for i in issues)
        positive_summary = None
        if len(issues) == 0:
            positive_summary = (
                "No major concerns found in the latest assessments. "
                "Weather conditions and soil moisture are within safe agronomic bounds. "
                "Crops and farm workers are operating in safe thermal environments."
            )

        return DashboardSummaryResponse(
            farm_id=farm_id,
            farm_name=farm_name,
            has_urgent_issues=has_urgent,
            total_issues_count=len(issues),
            issues=issues,
            positive_status_summary=positive_summary,
            assessed_at=datetime.now(timezone.utc).isoformat()
        )
