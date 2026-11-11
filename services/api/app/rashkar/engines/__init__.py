"""Pure-domain analytical engines recovered from RASHKAR 7b5641e."""

from .crop_heat_engine import CROP_SPECIES_PHYSIOLOGY, CropHeatEngine
from .crop_stage_service import STAGE_SENSITIVITY_MAP, CropStageService
from .forecast_scheduler import ForecastGridCache, grid_scheduler_cache
from .heat_ml_pipeline import HeatMLPipeline, WBGTLSTMModel, heat_ml_pipeline
from .income import (
    EXTENDED_OPPORTUNITY_CATALOG,
    IncomeEngine,
    IncomeFinancialService,
    OpportunityFeasibilityEngine,
    get_opportunity_by_id,
)
from .thermal_indices import (
    apply_topographic_lapse_downscaling,
    calculate_noaa_heat_index,
    calculate_utci_approx,
    compute_crop_heat_vulnerability_score,
    compute_personalized_worker_heat_strain_score,
)
from .wbgt_solver import (
    actual_vapor_pressure_kpa,
    calculate_wbgt,
    dew_point_c,
    solve_black_globe_temp,
    solve_natural_wet_bulb,
    vapor_pressure_deficit_kpa,
    vapor_pressure_kpa,
)
from .worker_heat_engine import (
    CLOTHING_ADJUSTMENT_VALUES,
    WORKLOAD_THRESHOLDS_ACCLIMATISED,
    WORKLOAD_THRESHOLDS_UNACCLIMATISED,
    WorkerHeatEngine,
    calculate_dew_point,
)
from .yield_risk_engine import (
    BUILTIN_APY_ALIAS_MAP,
    DISTRICT_IMD_NORMALS_MM,
    YieldRiskEngine,
)

__all__ = [
    "calculate_wbgt",
    "solve_natural_wet_bulb",
    "solve_black_globe_temp",
    "vapor_pressure_kpa",
    "actual_vapor_pressure_kpa",
    "vapor_pressure_deficit_kpa",
    "dew_point_c",
    "calculate_noaa_heat_index",
    "calculate_utci_approx",
    "apply_topographic_lapse_downscaling",
    "compute_personalized_worker_heat_strain_score",
    "compute_crop_heat_vulnerability_score",
    "HeatMLPipeline",
    "WBGTLSTMModel",
    "heat_ml_pipeline",
    "ForecastGridCache",
    "grid_scheduler_cache",
    "WorkerHeatEngine",
    "WORKLOAD_THRESHOLDS_ACCLIMATISED",
    "WORKLOAD_THRESHOLDS_UNACCLIMATISED",
    "CLOTHING_ADJUSTMENT_VALUES",
    "calculate_dew_point",
    "CropStageService",
    "STAGE_SENSITIVITY_MAP",
    "CropHeatEngine",
    "CROP_SPECIES_PHYSIOLOGY",
    "YieldRiskEngine",
    "DISTRICT_IMD_NORMALS_MM",
    "BUILTIN_APY_ALIAS_MAP",
    "EXTENDED_OPPORTUNITY_CATALOG",
    "get_opportunity_by_id",
    "IncomeEngine",
    "OpportunityFeasibilityEngine",
    "IncomeFinancialService",
]
