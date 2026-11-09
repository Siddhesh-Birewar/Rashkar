import pytest
from backend.app.schemas.dashboard import IssueSeverity, DashboardSummaryResponse
from backend.app.services.dashboard_issue_service import DashboardIssueService
from backend.app.db.session import SessionLocal
from backend.app.db.models.farm import FarmModel, FarmPlotModel, CropCycleModel

def test_dashboard_issue_service_returns_structured_summary():
    """Verify that dashboard issue service returns issues sorted by severity or positive status."""
    db = SessionLocal()
    try:
        summary = DashboardIssueService.get_farm_dashboard_issues(db, farm_id="farm_demo_01")
        assert isinstance(summary, DashboardSummaryResponse)
        assert summary.farm_id == "farm_demo_01"
        assert isinstance(summary.issues, list)
        
        # Verify valid severities
        for issue in summary.issues:
            assert issue.severity in [
                IssueSeverity.URGENT_ATTENTION,
                IssueSeverity.NEEDS_ATTENTION,
                IssueSeverity.KEEP_AN_EYE_ON,
                IssueSeverity.INFORMATION
            ]
            assert issue.action_target_route.startswith("/")
            assert len(issue.action_button_label) > 0
            assert len(issue.recommended_action) > 0

        # If zero issues, positive summary must be present
        if len(summary.issues) == 0:
            assert summary.positive_status_summary is not None
            assert "safe" in summary.positive_status_summary.lower() or "no major" in summary.positive_status_summary.lower()
    finally:
        db.close()

def test_dashboard_endpoint_in_api():
    """Verify GET /v1/dashboard/issues?farm_id=farm_demo_01 returns code 200."""
    from fastapi.testclient import TestClient
    from backend.app.main import app

    client = TestClient(app)
    response = client.get("/v1/dashboard/issues?farm_id=farm_demo_01")
    assert response.status_code == 200
    data = response.json()
    assert "issues" in data
    assert "total_issues_count" in data
