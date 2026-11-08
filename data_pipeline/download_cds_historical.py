"""
Copernicus Climate Data Store (CDS) Downloader for Pune Pilot Bounding Box.
Datasets:
  1. ERA5-Land Hourly Land Surface Reanalysis (S-02)
  2. AgERA5 Daily Agrometeorological Indicators (S-01)
Spatial extent: Pune Pilot Bounding Box [North 19.2, West 73.2, South 17.8, East 75.2]
"""

import sys
import hashlib
from pathlib import Path
import cdsapi

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings, BASE_DIR
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.db.session import SessionLocal

PUNE_BBOX = [19.2, 73.2, 17.8, 75.2]  # North, West, South, East

ERA5_DIR = settings.RAW_DATA_DIR / "WEATHER" / "ERA5_LAND"
AGERA5_DIR = settings.RAW_DATA_DIR / "WEATHER" / "AGERA5"
ERA5_DIR.mkdir(parents=True, exist_ok=True)
AGERA5_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def download_era5_land_heat_season(year="2024", month="05"):
    """Download hourly ERA5-Land for selected summer heatwave month in Pune pilot."""
    client = cdsapi.Client()
    output_nc = ERA5_DIR / f"era5_land_pune_heat_{year}_{month}.nc"

    if output_nc.exists() and output_nc.stat().st_size > 100000:
        print(f"[CDS] ERA5-Land file already exists: {output_nc}")
        return output_nc

    print(f"[CDS] Requesting ERA5-Land hourly surface data for Pune ({year}-{month})...")
    client.retrieve(
        "reanalysis-era5-land",
        {
            "variable": [
                "2m_temperature",
                "2m_dewpoint_temperature",
                "10m_u_component_of_wind",
                "10m_v_component_of_wind",
                "surface_solar_radiation_downwards",
                "surface_pressure"
            ],
            "year": year,
            "month": month,
            "day": [f"{d:02d}" for d in range(1, 16)],  # First half of May heatwave
            "time": [f"{h:02d}:00" for h in range(0, 24, 3)],  # 3-hourly time steps
            "area": PUNE_BBOX,
            "format": "netcdf"
        },
        str(output_nc)
    )

    sha = compute_sha256(output_nc)
    print(f"[CDS] Downloaded ERA5-Land: {output_nc} ({output_nc.stat().st_size / (1024*1024):.2f} MB, SHA: {sha[:16]}...)")

    # Register in DB
    db = SessionLocal()
    try:
        reg = DatasetRegisterRequest(
            dataset_id=f"S-02-ERA5-LAND-{year}-{month}",
            dataset_name=f"ERA5-Land Hourly Heat Season {year}-{month} (Pune Pilot)",
            publisher="Copernicus Climate Change Service (C3S) / ECMWF",
            source_url="https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land",
            classification="api",
            format="netcdf",
            temporal_coverage=f"{year}-{month}-01 to {year}-{month}-15",
            spatial_coverage="Pune Pilot Bounding Box (Lat 17.8-19.2 N, Lon 73.2-75.2 E)",
            spatial_resolution="0.1 deg (~9 km)",
            licence="Copernicus Open Access Licence",
            commercial_use_status="Permitted with attribution",
            storage_path=str(output_nc),
            provenance_metadata={
                "variables": [
                    "2m_temperature",
                    "2m_dewpoint_temperature",
                    "wind_speed",
                    "surface_solar_radiation_downwards",
                    "surface_pressure"
                ],
                "purpose": "Retrospective WBGT hourly proxy validation for heat stress"
            }
        )
        rec = RegistryService.register_dataset(db, reg, file_path=output_nc)
        print(f"[REGISTRY] Registered {rec.dataset_id} in database.")
    finally:
        db.close()

    return output_nc

def download_agera5_daily(year="2023"):
    """Download daily AgERA5 agricultural indicators for Pune pilot."""
    client = cdsapi.Client()
    output_nc = AGERA5_DIR / f"agera5_pune_daily_{year}.zip"

    if output_nc.exists() and output_nc.stat().st_size > 100000:
        print(f"[CDS] AgERA5 file already exists: {output_nc}")
        return output_nc

    print(f"[CDS] Requesting AgERA5 v2 daily indicators for Pune ({year})...")
    client.retrieve(
        "sis-agrometeorological-indicators",
        {
            "version": "2_0",
            "variable": "2m_temperature",
            "statistic": ["24_hour_mean", "24_hour_maximum", "24_hour_minimum"],
            "year": [str(year)],
            "month": ["07"],  # Peak vegetative / flowering month
            "day": [f"{d:02d}" for d in range(1, 32)],
            "area": PUNE_BBOX,
            "format": "zip"
        },
        str(output_nc)
    )

    sha = compute_sha256(output_nc)
    print(f"[CDS] Downloaded AgERA5: {output_nc} ({output_nc.stat().st_size / (1024*1024):.2f} MB, SHA: {sha[:16]}...)")

    # Register in DB
    db = SessionLocal()
    try:
        reg = DatasetRegisterRequest(
            dataset_id=f"S-01-AGERA5-{year}",
            dataset_name=f"AgERA5 Daily Kharif Weather {year} (Pune Pilot)",
            publisher="Copernicus C3S / ECMWF",
            source_url="https://cds.climate.copernicus.eu/datasets/sis-agrometeorological-indicators",
            classification="api",
            format="zip",
            temporal_coverage=f"{year}-06-01 to {year}-09-30",
            spatial_coverage="Pune Pilot Bounding Box (Lat 17.8-19.2 N, Lon 73.2-75.2 E)",
            spatial_resolution="0.1 deg (~10 km)",
            licence="Copernicus Open Access Licence",
            commercial_use_status="Permitted with attribution",
            storage_path=str(output_nc),
            provenance_metadata={
                "variables": ["2m_temp_mean", "2m_temp_max", "2m_temp_min"],
                "purpose": "Agro-climatic baseline and degree-day analysis"
            }
        )
        rec = RegistryService.register_dataset(db, reg, file_path=output_nc)
        print(f"[REGISTRY] Registered {rec.dataset_id} in database.")
    finally:
        db.close()

    return output_nc

if __name__ == "__main__":
    try:
        download_era5_land_heat_season("2024", "05")
    except Exception as e:
        print("[ERA5-LAND ERROR]", e)

    try:
        download_agera5_daily("2023")
    except Exception as e:
        print("[AGERA5 ERROR]", e)
