from enum import Enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone

class IssueSeverity(str, Enum):
    URGENT_ATTENTION = "URGENT_ATTENTION"
    NEEDS_ATTENTION = "NEEDS_ATTENTION"
    KEEP_AN_EYE_ON = "KEEP_AN_EYE_ON"
    INFORMATION = "INFORMATION"

class DashboardIssue(BaseModel):
    issue_id: str = Field(description="Unique issue identifier")
    domain: str = Field(description="Subsystem: worker_heat, crop_heat, yield_risk, season_integrity, weather")
    severity: IssueSeverity = Field(description="Prioritization level")
    title: str = Field(description="Farmer-friendly headline")
    summary: str = Field(description="Clear explanation of the problem")
    recommended_action: str = Field(description="Concrete action the farmer should take")
    action_target_route: str = Field(description="Flutter navigation route (e.g. /heat-safety, /my-crop)")
    action_button_label: str = Field(description="Label for 1-tap resolution button")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Supporting telemetry or threshold metrics")

class DashboardSummaryResponse(BaseModel):
    farm_id: str
    farm_name: str
    has_urgent_issues: bool
    total_issues_count: int
    issues: List[DashboardIssue] = Field(default_factory=list)
    positive_status_summary: Optional[str] = None
    assessed_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
