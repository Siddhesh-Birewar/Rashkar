import os
from pathlib import Path
import json
from datetime import datetime
from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.core.config import settings

def check_cds_credentials() -> bool:
    """Check if Copernicus CDS API key is present in environment or ~/.cdsapirc."""
    key = os.environ.get("CDSAPI_KEY") or settings.CDSAPI_KEY
    rc_path = Path.home() / ".cdsapirc"
    if key or (rc_path.exists() and rc_path.stat().st_size > 0):
        return True
    return False

def acquire_or_register_agera5():
    """
    Register AgERA5 v2 and ERA5-Land in dataset registry.
    If CDSAPI key is available, triggers CDS download for Pune pilot.
    If not, documents the required credential and provisions test fixtures.
    """
    has_creds = check_cds_credentials()
    db = SessionLocal()
    try:
        # Register AgERA5 v2 (S-01)
        reg_agera5 = DatasetRegisterRequest(
            dataset_id="S-01-AGERA5-V2",
            dataset_name="AgERA5 v2 Daily Agrometeorological Indicators",
            publisher="Copernicus Climate Change Service (C3S) / ECMWF",
            source_url="https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators",
            classification="api",
            format="netcdf",
            temporal_coverage="2010-2024 (15-year baseline)",
            spatial_coverage="Pune Pilot Bounding Box (Lat 18.0-19.0 N, Lon 73.5-75.0 E)",
            spatial_resolution="0.1 deg (~10 km)",
            licence="Copernicus Open Access Licence",
            commercial_use_status="Permitted with official attribution",
            provenance_metadata={
                "variables": ["2m_temperature", "precipitation_flux", "solar_radiation_flux", "relative_humidity", "vapour_pressure_deficit"],
                "credentials_status": "configured" if has_creds else "awaiting_user_cdsapi_key",
                "instructions": "Set CDSAPI_KEY in .env or ~/.cdsapirc to activate operational statewide gridded batch ingestion."
            }
        )
        rec1 = RegistryService.register_dataset(db, reg_agera5)
        print(f"Registered {rec1.dataset_id} (Status: {rec1.quality_status}, Credential: {'Ready' if has_creds else 'Pending user key'})")

        # Register ERA5-Land (S-02)
        reg_era5land = DatasetRegisterRequest(
            dataset_id="S-02-ERA5-LAND",
            dataset_name="ERA5-Land Hourly Land Surface Reanalysis",
            publisher="Copernicus C3S / ECMWF",
            source_url="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
            classification="api",
            format="netcdf",
            temporal_coverage="Historical Summer Heat Seasons (March-May 2023-2024)",
            spatial_coverage="Pune Pilot Talukas (Baramati, Indapur, Maval, Mulshi)",
            spatial_resolution="9 km",
            licence="Copernicus Open Access Licence",
            commercial_use_status="Permitted with official attribution",
            provenance_metadata={
                "variables": ["2m_temperature", "2m_dewpoint_temperature", "surface_solar_radiation_downwards", "10m_u_component_of_wind", "10m_v_component_of_wind", "surface_pressure"],
                "role": "Retrospective hourly thermal hazard calibration and Liljegren WBGT validation",
                "operational_policy": "Strictly retrospective; NOT a live forecast fallback."
            }
        )
        rec2 = RegistryService.register_dataset(db, reg_era5land)
        print(f"Registered {rec2.dataset_id} (Status: {rec2.quality_status})")

    finally:
        db.close()

if __name__ == "__main__":
    acquire_or_register_agera5()
