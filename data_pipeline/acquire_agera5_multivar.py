"""
AgERA5 v2 Multi-Variable Daily Agrometeorological Data Acquisition Pipeline.

Retrieves official ECMWF AgERA5 v2 indicators from Copernicus Climate Data Store:
- 2m Maximum, Minimum, and Mean Temperature
- Precipitation flux
- Solar radiation flux
- 10m Wind speed
- 2m Relative humidity (morning 06:00 and afternoon 12:00)
- Reference evapotranspiration
- Vapour pressure deficit at maximum temperature

Spatial Domain: Pune Pilot Bounding Box [17.8° - 19.2°N, 73.2° - 75.2°E]
Version: 2_0
"""

import os
import sys
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime
import cdsapi

from backend.app.core.config import settings, BASE_DIR
from backend.app.db.session import SessionLocal
from backend.app.db.models.registry import DatasetRegistryModel
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.services.registry_service import RegistryService

AGERA5_RAW_DIR = BASE_DIR / "data" / "01_raw_immutable" / "WEATHER" / "AGERA5"
AGERA5_RAW_DIR.mkdir(parents=True, exist_ok=True)

# Pilot bounding box: [North, West, South, East]
PUNE_BBOX = [19.2, 73.2, 17.8, 75.2]

DATASET_NAME = "sis-agrometeorological-indicators"

# Variable configurations for AgERA5 v2
VARIABLES_CONFIG = {
    "2m_temperature": {
        "dataset_id_suffix": "TEMP-2023",
        "name": "AgERA5 v2 Daily 2m Temperature (Mean, Max, Min)",
        "params": {
            "variable": "2m_temperature",
            "statistic": ["24_hour_mean", "24_hour_maximum", "24_hour_minimum"],
        }
    },
    "precipitation_flux": {
        "dataset_id_suffix": "PRECIP-2023",
        "name": "AgERA5 v2 Daily Precipitation Flux",
        "params": {
            "variable": "precipitation_flux",
        }
    },
    "solar_radiation_flux": {
        "dataset_id_suffix": "SOLAR-2023",
        "name": "AgERA5 v2 Daily Solar Radiation Flux",
        "params": {
            "variable": "solar_radiation_flux",
        }
    },
    "10m_wind_speed": {
        "dataset_id_suffix": "WIND-2023",
        "name": "AgERA5 v2 Daily 10m Wind Speed",
        "params": {
            "variable": "10m_wind_speed",
            "statistic": ["24_hour_mean"],
        }
    },
    "2m_relative_humidity": {
        "dataset_id_suffix": "RH-2023",
        "name": "AgERA5 v2 Daily 2m Relative Humidity",
        "params": {
            "variable": "2m_relative_humidity",
            "time": ["06_00", "12_00"],
        }
    },
    "reference_evapotranspiration": {
        "dataset_id_suffix": "ET0-2023",
        "name": "AgERA5 v2 Daily Reference Evapotranspiration",
        "params": {
            "variable": "reference_evapotranspiration",
        }
    },
    "vapour_pressure_deficit_at_maximum_temperature": {
        "dataset_id_suffix": "VPD-2023",
        "name": "AgERA5 v2 Daily Vapour Pressure Deficit at Max Temp",
        "params": {
            "variable": "vapour_pressure_deficit_at_maximum_temperature",
        }
    }
}


def download_agera5_variable(var_key: str, year: str = "2023", month: str = "05"):
    """Downloads specified AgERA5 variable from Copernicus CDS."""
    cfg = VARIABLES_CONFIG[var_key]
    out_zip = AGERA5_RAW_DIR / f"agera5_{var_key}_{year}_{month}.zip"

    if out_zip.exists() and out_zip.stat().st_size > 1000:
        print(f"[EXISTS] {out_zip.name} ({out_zip.stat().st_size / 1024:.1f} KB)")
        return out_zip

    c = cdsapi.Client()
    req = {
        "version": "2_0",
        "year": year,
        "month": month,
        "day": [f"{d:02d}" for d in range(1, 16)],  # 15 days representative slice
        "area": PUNE_BBOX,
        **cfg["params"]
    }

    print(f"\n[CDS] Requesting AgERA5 v2 variable '{var_key}' for {year}-{month}...")
    c.retrieve(DATASET_NAME, req, str(out_zip))
    print(f"[CDS] Downloaded {out_zip.name} ({out_zip.stat().st_size / 1024:.1f} KB)")
    return out_zip


def verify_and_register_agera5(db, var_key: str, zip_path: Path, year: str = "2023", month: str = "05"):
    """Inspects contents and registers AgERA5 variable."""
    cfg = VARIABLES_CONFIG[var_key]
    dataset_id = f"S-01-AGERA5-{cfg['dataset_id_suffix']}"

    with zipfile.ZipFile(zip_path, "r") as z:
        members = z.namelist()
        nc_count = len([m for m in members if m.endswith(".nc")])

    sha = hashlib.sha256(zip_path.read_bytes()).hexdigest()

    reg_req = DatasetRegisterRequest(
        dataset_id=dataset_id,
        dataset_name=f"{cfg['name']} ({year}-{month} Pune)",
        publisher="ECMWF Copernicus Climate Change Service",
        source_url="https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators",
        classification="api",
        format="zip_netcdf",
        temporal_coverage=f"{year}-{month}-01 to {year}-{month}-15",
        spatial_coverage="Pune Pilot Bounding Box (17.8-19.2 N, 73.2-75.2 E)",
        spatial_resolution="0.1 deg (~10 km)",
        licence="Copernicus Open Access / ECMWF Licence",
        commercial_use_status="Permitted with attribution",
        storage_path=str(zip_path),
        row_count=nc_count,
        provenance_metadata={
            "variable_key": var_key,
            "version": "2_0",
            "netcdf_slices_count": nc_count,
            "files_sample": members[:5],
            "sha256": sha
        }
    )
    rec = RegistryService.register_dataset(db, reg_req, file_path=zip_path)
    print(f"[REGISTRY] Registered {dataset_id}: {rec.dataset_name}")
    return rec


def acquire_all_agera5_variables():
    """Acquires all 7 requested AgERA5 variables for the Pune pilot."""
    db = SessionLocal()
    try:
        for var_key in VARIABLES_CONFIG.keys():
            zip_p = download_agera5_variable(var_key, year="2023", month="05")
            verify_and_register_agera5(db, var_key, zip_p, year="2023", month="05")
    finally:
        db.close()


if __name__ == "__main__":
    acquire_all_agera5_variables()
