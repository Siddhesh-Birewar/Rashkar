import pytest
from pathlib import Path
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.services.registry_service import RegistryService

def test_registry_lifecycle(client, tmp_path):
    # Create a temporary mock data file
    dummy_file = tmp_path / "test_rainfall.csv"
    dummy_file.write_text("date,rainfall_mm\n2024-07-01,12.5\n", encoding="utf-8")

    # Register dataset via API
    payload = {
        "dataset_id": "TEST-RAIN-01",
        "dataset_name": "Test Pune AWS Rainfall",
        "publisher": "IMD Test Service",
        "classification": "direct_download",
        "format": "csv",
        "temporal_coverage": "2024",
        "spatial_coverage": "Pune District",
        "licence": "Open Access",
        "storage_path": str(dummy_file),
        "row_count": 1
    }

    response = client.post("/v1/registry/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["dataset_id"] == "TEST-RAIN-01"
    assert data["quality_status"] == "pending_validation"

    # Verify SHA-256 computation in Service
    checksum = RegistryService.calculate_sha256(dummy_file)
    assert len(checksum) == 64

    # List datasets
    list_res = client.get("/v1/registry/")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(d["dataset_id"] == "TEST-RAIN-01" for d in items)

    # Get single dataset
    get_res = client.get("/v1/registry/TEST-RAIN-01")
    assert get_res.status_code == 200
    assert get_res.json()["publisher"] == "IMD Test Service"
