"""
CropNet AI — Farm Context Validator.

Validates farm inputs, detects physical and chemical input anomalies,
distinguishes laboratory from spatial estimates, and requests clarification
for unusual conditions without automatically invalidating entire requests.
Phase 5.1.2: Hardened rules; unusual physical combinations trigger clarification
rather than automatic request rejection.
"""
from typing import List, Dict, Any, Tuple
from cropnet.services.api.app.schemas.agriculture_intelligence import FarmContextInput, SoilDataProvenance


PILOT_TALUKAS = {"baramati", "indapur", "maval", "mulshi"}


class ValidationResult:
    def __init__(self):
        self.is_valid: bool = True
        self.is_empty_context: bool = False
        self.needs_clarification: bool = False
        self.contradictions: List[str] = []
        self.missing_parameters: List[str] = []
        self.warnings: List[str] = []
        self.resolved_taluka: str = None


class FarmContextValidator:
    """
    Validates structured farm context before agronomic rules are evaluated.
    """

    @staticmethod
    def validate(ctx: FarmContextInput) -> ValidationResult:
        res = ValidationResult()

        # 1. Check for complete emptiness
        provided_fields = [
            ctx.soil_ph, ctx.soil_organic_carbon_pct, ctx.soil_texture, ctx.soil_depth_cm,
            ctx.drainage, ctx.available_nitrogen_kg_ha, ctx.irrigation_available,
            ctx.taluka, ctx.latitude, ctx.target_crops, ctx.target_season
        ]
        if all(v is None for v in provided_fields):
            res.is_empty_context = True
            res.is_valid = False
            res.missing_parameters.extend(["taluka", "cropping_season", "soil_type", "irrigation_source"])
            res.warnings.append("Context is 100% empty. Mandatory abstention triggered.")
            return res

        # 2. Taluka Normalization & Validation
        if ctx.taluka:
            clean_taluka = ctx.taluka.strip().lower()
            res.resolved_taluka = clean_taluka
            if clean_taluka not in PILOT_TALUKAS:
                res.warnings.append(
                    f"Taluka '{ctx.taluka}' is outside the 4 pilot talukas (Baramati, Indapur, Maval, Mulshi). "
                    "Rules will evaluate under unverified regional conditions."
                )
        else:
            res.missing_parameters.append("taluka")

        # 3. Anomaly Detection: Soil Hydrology (Phase 5.1.2: Clarification over Rejection)
        query_lower = (ctx.user_query or "").lower()
        if ctx.soil_texture:
            tex_lower = ctx.soil_texture.lower()
            if "sand" in tex_lower or "coarse" in tex_lower:
                if (ctx.standing_water_days and ctx.standing_water_days >= 7) or (
                    "water stand" in query_lower or "standing water" in query_lower or "stands on the surface" in query_lower or "पाणी साचून" in query_lower
                ):
                    res.contradictions.append(
                        f"Input Clarification Required: Coarse sandy soil reported with {ctx.standing_water_days or 'persistent'} days "
                        "standing surface water. While coarse sand macropores normally facilitate rapid infiltration, "
                        "water accumulation can occur over an impermeable subsoil hardpan, clay lenses, high water table, "
                        "or low-lying surface runoff depression. Clarification of subsoil compaction is advised."
                    )
                    res.needs_clarification = True

        if ctx.soil_texture and ctx.drainage:
            tex_lower = ctx.soil_texture.lower()
            drain_lower = ctx.drainage.lower()
            if ("sand" in tex_lower or "coarse" in tex_lower) and ("waterlog" in drain_lower or "poor" in drain_lower):
                res.contradictions.append(
                    "Input Clarification Required: Coarse sand texture reported with 'Poor / Waterlogged' drainage. "
                    "This combination suggests a restrictive subsurface layer or external runoff catchment. "
                    "Subsurface barrier inspection recommended."
                )
                res.needs_clarification = True

        # 4. Anomaly Detection: pH Misclassification & Hazardous Lime Application
        if ctx.user_query and ctx.soil_ph:
            query_lower = ctx.user_query.lower()
            if ctx.soil_ph >= 7.8 and ("acidic" in query_lower or "आम्ल" in query_lower or "lime" in query_lower or "चुना" in query_lower):
                res.contradictions.append(
                    f"Chemical contradiction: Soil pH is {ctx.soil_ph} (alkaline/calcareous), but user describes "
                    "it as acidic or plans to apply agricultural lime (CaCO3). Lime application on pH > 7.8 is strictly hazardous and will aggravate alkalinity."
                )
                res.needs_clarification = True

        # 5. Total Nitrogen vs Available Nitrogen Guard
        if ctx.total_nitrogen_pct is not None and ctx.available_nitrogen_kg_ha is None:
            res.warnings.append(
                f"Total Nitrogen ({ctx.total_nitrogen_pct}%) represents organically bound nitrogen, NOT plant-available food. "
                "Available Nitrogen (alkaline permanganate extract) is missing. Cannot calculate quantitative urea dosages."
            )
            res.missing_parameters.append("available_nitrogen_kg_ha")

        # 6. Canal Zone Salinity & Water Table Guard
        if res.resolved_taluka in ("indapur", "baramati") and ctx.irrigation_source == "canal":
            if ctx.electrical_conductivity_ds_m is None:
                res.missing_parameters.append("electrical_conductivity_ds_m")
                res.warnings.append(
                    "Canal command areas in Baramati/Indapur are vulnerable to canal seepage salinity. "
                    "Electrical Conductivity (EC) test is required before certifying salt-sensitive crops."
                )

        # 7. Unchecked Well Water Guard
        if ctx.irrigation_source in ("well", "borewell") and ctx.irrigation_water_salinity_tested is False:
            res.missing_parameters.append("irrigation_water_ec_ds_m")
            res.warnings.append(
                "Groundwater in semi-arid Vertisols often carries high salinity (EC > 1.5 dS/m) or sodicity. "
                "Water testing for EC and SAR is recommended."
            )

        # 8. Missing Basic Diagnostic Parameters
        if ctx.soil_depth_cm is None:
            res.missing_parameters.append("soil_depth_cm")
        if ctx.drainage is None:
            res.missing_parameters.append("drainage")

        return res
