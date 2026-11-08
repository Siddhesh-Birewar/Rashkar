from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class RiskItem(BaseModel):
    risk_dimension: str
    risk_level: str  # low, moderate, high, extreme
    time_horizon: str
    impact_severity: str
    confidence: str
    drivers: List[str]
    evidence_provenance: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]

class YieldRiskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    farm_id: str
    plot_id: str
    crop_code: str
    generated_at_utc: str
    timezone: str
    coverage: Dict[str, Any]
    crop_stage: Dict[str, Any]
    risks: List[RiskItem]
    yield_baseline: Dict[str, Any]
