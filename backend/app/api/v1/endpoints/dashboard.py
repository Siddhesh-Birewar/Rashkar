from typing import Annotated
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.schemas.dashboard import DashboardSummaryResponse
from backend.app.services.dashboard_issue_service import DashboardIssueService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/issues", response_model=DashboardSummaryResponse)
def get_dashboard_issues(
    farm_id: Annotated[str, Query(description="Farm ID to evaluate")] = "farm_demo_01",
    db: Session = Depends(get_db)
) -> DashboardSummaryResponse:
    """Retrieve prioritized farm issues or safe farm status for the simplified home screen."""
    return DashboardIssueService.get_farm_dashboard_issues(db=db, farm_id=farm_id)
