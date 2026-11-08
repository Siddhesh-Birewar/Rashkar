"""
Acquire genuine IMD 0.25-degree daily gridded rainfall NetCDF files for multi-year historical analysis.
Source: India Meteorological Department (IMD) Pune, National Climate Centre.
Endpoint: https://imdpune.gov.in/cmpg/Griddata/RF25.php
"""

import sys
import hashlib
from pathlib import Path
import requests
import xarray as xr

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings, BASE_DIR
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.db.session import SessionLocal

IMD_URL = "https://imdpune.gov.in/cmpg/Griddata/RF25.php"
RAW_DIR = settings.RAW_DATA_DIR / "WEATHER" / "IMD_RAINFALL"
RAW_DIR.mkdir(parents=True, exist_ok=True)

def download_imd_year(year: int) -> Path:
    target_path = RAW_DIR / f"ind{year}_rfp25.nc"
    if target_path.exists() and target_path.stat().st_size > 10000000:
        print(f"[IMD] Year {year} already exists: {target_path} ({target_path.stat().st_size / (1024*1024):.2f} MB)")
        return target_path

    print(f"[IMD] Downloading Year {year} from IMD Pune...")
    resp = requests.post(IMD_URL, data={"RF25": str(year)}, stream=True, timeout=90)
    resp.raise_for_status()

    with open(target_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

    size_mb = target_path.stat().st_size / (1024 * 1024)
    print(f"[IMD] Year {year} saved: {target_path} ({size_mb:.2f} MB)")
    return target_path

def acquire_imd_years(years=[2023, 2022, 2021, 2020]):
    db = SessionLocal()
    try:
        for yr in years:
            nc_path = download_imd_year(yr)
            
            # Verify valid NetCDF
            ds = xr.open_dataset(nc_path)
            time_steps = len(ds["TIME"]) if "TIME" in ds else (366 if yr % 4 == 0 else 365)
            ds.close()

            # Register in database
            reg_id = f"S-03-IMD-RAIN-{yr}"
            reg_request = DatasetRegisterRequest(
                dataset_id=reg_id,
                dataset_name=f"IMD 0.25° Daily Gridded Rainfall {yr}",
                publisher="Climate Research and Services, IMD Pune",
                source_url=IMD_URL,
                classification="direct_download",
                format="netcdf",
                temporal_coverage=f"{yr}-01-01 to {yr}-12-31",
                spatial_coverage="India (0.25 degree grid)",
                spatial_resolution="0.25 deg (~25 km)",
                licence="Government of India / IMD Open Data",
                commercial_use_status="Permitted with citation",
                storage_path=str(nc_path),
                row_count=time_steps,
                provenance_metadata={
                    "variable_name": "RAINFALL",
                    "unit": "mm/day",
                    "source_grid": "IMD 0.25 x 0.25"
                }
            )
            record = RegistryService.register_dataset(db, reg_request, file_path=nc_path)
            print(f"[REGISTRY] Registered {record.dataset_id} successfully (SHA: {record.sha256_checksum[:16]}...)")
    finally:
        db.close()

if __name__ == "__main__":
    acquire_imd_years([2023, 2022, 2021, 2020])
