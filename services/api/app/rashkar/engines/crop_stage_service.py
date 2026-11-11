"""Phenological crop stage estimation service based on DAS and farmer overrides."""

from datetime import date
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session

from ..models import RashkarCropStageModel
from ..timezone import now_ist


# Stage sensitivity lookup preserved verbatim from 7b5641e/backend/app/db/init_db.py
# because RashkarCropStageModel stores normalized columns without sensitivity columns.
STAGE_SENSITIVITY_MAP: Dict[Tuple[str, str], Dict[str, str]] = {
    ("soybean", "VEGETATIVE"): {
        "heat_sensitivity": "low",
        "drought_sensitivity": "medium",
        "excess_water_sensitivity": "high",
    },
    ("soybean", "R1_FLOWERING"): {
        "heat_sensitivity": "critical",
        "drought_sensitivity": "critical",
        "excess_water_sensitivity": "medium",
    },
    ("soybean", "R3_POD_FILLING"): {
        "heat_sensitivity": "high",
        "drought_sensitivity": "critical",
        "excess_water_sensitivity": "low",
    },
    ("soybean", "R7_MATURITY"): {
        "heat_sensitivity": "low",
        "drought_sensitivity": "low",
        "excess_water_sensitivity": "high",
    },
    ("cotton", "VEGETATIVE"): {
        "heat_sensitivity": "medium",
        "drought_sensitivity": "medium",
        "excess_water_sensitivity": "high",
    },
    ("cotton", "FLOWERING_BOLL_DEV"): {
        "heat_sensitivity": "critical",
        "drought_sensitivity": "critical",
        "excess_water_sensitivity": "high",
    },
}


def _stage_sensitivities(crop_code: str, stage_code: str) -> Dict[str, str]:
    key = (crop_code.lower(), stage_code)
    return STAGE_SENSITIVITY_MAP.get(
        key,
        {
            "heat_sensitivity": "medium",
            "drought_sensitivity": "medium",
            "excess_water_sensitivity": "medium",
        },
    )


class CropStageService:
    """Estimates active crop phenological stage from sowing date or farmer confirmation."""

    @staticmethod
    def estimate_crop_stage(
        db: Session,
        crop_code: str,
        sowing_date: Optional[date],
        farmer_confirmed_stage: Optional[str] = None,
        as_of_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        Estimate current phenological stage based on sowing date and SAU reference durations.
        Farmer confirmed stage takes strict precedence if provided.
        """
        today = as_of_date or now_ist().date()
        das = max(0, (today - sowing_date).days) if sowing_date is not None else 0

        crop_norm = (crop_code or "").lower()
        stages = (
            db.query(RashkarCropStageModel)
            .filter(RashkarCropStageModel.crop_code == crop_norm)
            .order_by(RashkarCropStageModel.sequence_order)
            .all()
        )

        if not stages:
            return {
                "stage_code": farmer_confirmed_stage or "GENERAL_GROWTH",
                "stage_name_en": farmer_confirmed_stage or "Vegetative / General Growth",
                "stage_name_mr": "वाढीची अवस्था",
                "days_after_sowing": das,
                "stage_source": (
                    "farmer_confirmed"
                    if farmer_confirmed_stage
                    else "generic_heuristic"
                ),
                "farmer_confirmed": bool(farmer_confirmed_stage),
                "is_expired": False,
                "season_status": "ACTIVE",
                "confidence": "high" if farmer_confirmed_stage else "low",
                "heat_sensitivity": "medium",
                "drought_sensitivity": "medium",
                "excess_water_sensitivity": "medium",
            }

        if farmer_confirmed_stage:
            norm_target = farmer_confirmed_stage.lower().replace("stage_", "")
            matched = next(
                (
                    s
                    for s in stages
                    if s.stage_code.lower() == farmer_confirmed_stage.lower()
                    or norm_target in s.stage_code.lower()
                    or s.stage_code.lower() in norm_target
                ),
                None,
            )
            if matched:
                sens = _stage_sensitivities(crop_norm, matched.stage_code)
                return {
                    "stage_code": matched.stage_code,
                    "stage_name_en": matched.stage_name_en,
                    "stage_name_mr": matched.stage_name_mr,
                    "days_after_sowing": das,
                    "stage_source": "farmer_confirmed",
                    "farmer_confirmed": True,
                    "is_expired": False,
                    "season_status": "ACTIVE",
                    "confidence": "high",
                    **sens,
                }

        max_das_end = max(s.typical_das_end for s in stages)
        if sowing_date is not None and das > max_das_end + 15:
            return {
                "stage_code": None,
                "stage_name_en": "Crop Season Expired (DAS exceeded typical season)",
                "stage_name_mr": "हंगाम समाप्त झाला",
                "days_after_sowing": das,
                "stage_source": "expired_crop_season",
                "farmer_confirmed": False,
                "is_expired": True,
                "season_status": "EXPIRED",
                "max_typical_das": max_das_end,
                "confidence": "high",
                "heat_sensitivity": "none",
                "drought_sensitivity": "none",
                "excess_water_sensitivity": "none",
            }

        matched_stage = stages[0]
        for s in stages:
            if das >= s.typical_das_start:
                matched_stage = s
            if das <= s.typical_das_end:
                matched_stage = s
                break

        sens = _stage_sensitivities(crop_norm, matched_stage.stage_code)
        return {
            "stage_code": matched_stage.stage_code,
            "stage_name_en": matched_stage.stage_name_en,
            "stage_name_mr": matched_stage.stage_name_mr,
            "days_after_sowing": das,
            "stage_source": (
                "sowing_date_estimate"
                if sowing_date is not None
                else "default_initial_stage"
            ),
            "farmer_confirmed": False,
            "is_expired": False,
            "season_status": "ACTIVE",
            "confidence": "medium" if sowing_date is not None else "low",
            **sens,
        }

    estimate_growth_stage = estimate_crop_stage


__all__ = ["CropStageService", "STAGE_SENSITIVITY_MAP"]
