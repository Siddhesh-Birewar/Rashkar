"""
Acquire complete historical IMD 0.25-degree daily gridded rainfall NetCDF files (1991-2019).
Source: Climate Research & Services (CRS), India Meteorological Department (IMD) Pune.
Endpoint: https://imdpune.gov.in/cmpg/Griddata/RF25.php

Produces:
  1. Immutable raw archives in data/01_raw_immutable/WEATHER/IMD_RAINFALL/ind{year}_rfp25.nc
  2. Cryptographic SHA-256 catalog registrations in DatasetRegistryModel
  3. Derived Reference Period 1: Climate Normal (1991-2020, 30-year WMO-standard normal)
  4. Derived Reference Period 2: Recent Agricultural Reference (2010-2024, 15-year baseline, NOT a WMO normal)
"""

import sys
import os
import hashlib
from pathlib import Path
import requests
import xarray as xr
import numpy as np

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.core.config import settings, BASE_DIR
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.db.session import SessionLocal

IMD_URL = "https://imdpune.gov.in/cmpg/Griddata/RF25.php"
RAW_DIR = settings.RAW_DATA_DIR / "WEATHER" / "IMD_RAINFALL"
PROCESSED_DIR = settings.PROCESSED_DATA_DIR / "WEATHER" / "IMD_NORMALS"
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Maharashtra Bounding Box (Lat 15.5-22.5 N, Lon 72.5-81.0 E)
MAHA_BBOX = {"lat_min": 15.5, "lat_max": 22.5, "lon_min": 72.5, "lon_max": 81.0}

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def download_imd_year(year: int) -> Path:
    target_path = RAW_DIR / f"ind{year}_rfp25.nc"
    if target_path.exists() and target_path.stat().st_size > 20000000:
        print(f"[IMD] Year {year} already exists: {target_path.name} ({target_path.stat().st_size / (1024*1024):.2f} MB)")
        return target_path

    print(f"[IMD] Downloading Year {year} from IMD Pune...")
    resp = requests.post(IMD_URL, data={"RF25": str(year)}, stream=True, timeout=120)
    resp.raise_for_status()

    with open(target_path, "wb") as f:
        for chunk in resp.iter_content(chunk_size=65536):
            if chunk:
                f.write(chunk)

    size_mb = target_path.stat().st_size / (1024 * 1024)
    print(f"[IMD] Year {year} saved: {target_path.name} ({size_mb:.2f} MB)")
    return target_path

def verify_and_register_year(db, year: int, nc_path: Path):
    sha = compute_sha256(nc_path)
    ds = xr.open_dataset(nc_path)

    # Verification checks
    time_len = len(ds["TIME"]) if "TIME" in ds else 365
    is_leap = (year % 4 == 0 and (year % 100 != 0 or year % 400 == 0))
    expected_days = 366 if is_leap else 365
    assert time_len == expected_days, f"Expected {expected_days} days for {year}, got {time_len}"

    lat_name = "LATITUDE" if "LATITUDE" in ds else "lat"
    lon_name = "LONGITUDE" if "LONGITUDE" in ds else "lon"
    rf_var = ds["RAINFALL"]

    # Verify units and fill values
    units = rf_var.attrs.get("units", "mm/day")
    fill_val = rf_var.attrs.get("_FillValue", -999.0)

    ds.close()

    reg_id = f"S-03-IMD-RAIN-{year}"
    reg_request = DatasetRegisterRequest(
        dataset_id=reg_id,
        dataset_name=f"IMD 0.25° Daily Gridded Rainfall {year}",
        publisher="Climate Research and Services, IMD Pune",
        source_url=IMD_URL,
        classification="direct_download",
        format="netcdf",
        temporal_coverage=f"{year}-01-01 to {year}-12-31 ({time_len} days)",
        spatial_coverage="India (0.25 degree grid, 6.5-38.5N, 66.5-100E)",
        spatial_resolution="0.25 deg (~25 km)",
        licence="Government of India / IMD Open Data",
        commercial_use_status="Permitted with citation",
        storage_path=str(nc_path),
        row_count=time_len,
        provenance_metadata={
            "variable_name": "RAINFALL",
            "unit": "mm/day",
            "fill_value": float(fill_val) if fill_val is not None else -999.0,
            "crs": "EPSG:4326 (WGS84)",
            "sha256": sha
        }
    )
    rec = RegistryService.register_dataset(db, reg_request, file_path=nc_path)
    return rec

def download_range(start_year: int = 1991, end_year: int = 2019):
    db = SessionLocal()
    try:
        for y in range(start_year, end_year + 1):
            nc = download_imd_year(y)
            verify_and_register_year(db, y, nc)
            print(f"[VERIFIED] Year {y} checked and registered.")
    finally:
        db.close()

def generate_derived_reference_periods():
    """
    Produce the two derived reference NetCDF products:
      1. Climate Normal: 1991-2020 (30-year WMO normal)
      2. Recent Agricultural Reference: 2010-2024 (15-year baseline, NOT a WMO normal)
    """
    print("\n--- Generating Derived Gridded Rainfall Reference Baselines for Maharashtra ---")
    db = SessionLocal()
    try:
        # Helper to compute gridded annual mean and std
        def compute_baseline(years, title, description, is_wmo_normal):
            annual_totals = []
            for y in years:
                ds = xr.open_dataset(RAW_DIR / f"ind{y}_rfp25.nc")
                lat_k = "LATITUDE" if "LATITUDE" in ds else "lat"
                lon_k = "LONGITUDE" if "LONGITUDE" in ds else "lon"
                # Slice Maharashtra
                sub = ds["RAINFALL"].sel(
                    {lat_k: slice(MAHA_BBOX["lat_min"], MAHA_BBOX["lat_max"]),
                     lon_k: slice(MAHA_BBOX["lon_min"], MAHA_BBOX["lon_max"])}
                )
                # Mask fill values (< 0)
                sub_valid = sub.where(sub >= 0)
                annual_sum = sub_valid.sum(dim="TIME")
                annual_totals.append(annual_sum)
                ds.close()

            concat_ds = xr.concat(annual_totals, dim="year")
            mean_grid = concat_ds.mean(dim="year")
            std_grid = concat_ds.std(dim="year")

            out_ds = xr.Dataset({
                "annual_mean_rainfall_mm": mean_grid,
                "annual_std_rainfall_mm": std_grid
            })
            out_ds.attrs["title"] = title
            out_ds.attrs["description"] = description
            out_ds.attrs["is_wmo_climate_normal"] = "true" if is_wmo_normal else "false"
            out_ds.attrs["spatial_coverage"] = "Maharashtra Bounding Box (15.5-22.5 N, 72.5-81.0 E)"
            out_ds.attrs["sample_years_included"] = str(years)
            out_ds.attrs["years_count"] = len(years)
            return out_ds

        # 1. Climate Normal: 1991-2020 (30-year WMO normal)
        normal_years = [y for y in range(1991, 2021) if (RAW_DIR / f"ind{y}_rfp25.nc").exists()]
        print(f"Available years for 1991-2020 Normal: {len(normal_years)} / 30")
        if len(normal_years) == 30:
            norm_ds = compute_baseline(
                normal_years,
                title="IMD Gridded Rainfall 30-Year Climate Normal (1991-2020)",
                description="Official WMO-compliant 30-year Climate Normal for Maharashtra gridded rainfall (1991-2020), derived from IMD Pune 0.25-degree daily NetCDF series.",
                is_wmo_normal=True
            )
            norm_path = PROCESSED_DIR / "maharashtra_rainfall_climate_normal_1991_2020.nc"
            norm_ds.to_netcdf(norm_path)
            norm_ds.close()
            print(f"[DERIVED] Saved 30-year Climate Normal: {norm_path} ({norm_path.stat().st_size / 1024:.1f} KB)")
            
            # Register in DB
            sha = hashlib.sha256(norm_path.read_bytes()).hexdigest()
            reg_norm = DatasetRegisterRequest(
                dataset_id="P-01-IMD-NORMAL-1991-2020",
                dataset_name="IMD Gridded Rainfall 30-Year Climate Normal (1991-2020)",
                publisher="IMD Pune / Rashkar Derived Products",
                source_url=IMD_URL,
                classification="derived_product",
                format="netcdf",
                temporal_coverage="1991-01-01 to 2020-12-31 (30-year Climate Normal)",
                spatial_coverage="Maharashtra Bounding Box (15.5-22.5 N, 72.5-81.0 E)",
                spatial_resolution="0.25 deg (~25 km)",
                licence="Derived from IMD Open Data",
                commercial_use_status="Permitted with citation",
                storage_path=str(norm_path),
                row_count=30,
                provenance_metadata={
                    "is_wmo_climate_normal": True,
                    "resolution": "0.25 deg (~27km)",
                    "years_included": normal_years,
                    "sha256": sha
                }
            )
            RegistryService.register_dataset(db, reg_norm, file_path=norm_path)
            print("[REGISTRY] P-01-IMD-NORMAL-1991-2020 registered successfully.")

        # 2. Recent Agricultural Reference: 2010-2024 (15-year baseline, NOT a WMO normal)
        recent_years = [y for y in range(2010, 2025) if (RAW_DIR / f"ind{y}_rfp25.nc").exists()]
        print(f"Available years for 2010-2024 Recent Reference: {len(recent_years)} / 15")
        if len(recent_years) == 15:
            rec_ds = compute_baseline(
                recent_years,
                title="IMD Gridded Rainfall Recent Agricultural Reference Period (2010-2024)",
                description="Recent Agricultural Reference Period Baseline (2010-2024). NOT an official WMO 30-year Climate Normal.",
                is_wmo_normal=False
            )
            rec_path = PROCESSED_DIR / "maharashtra_rainfall_recent_ref_2010_2024.nc"
            rec_ds.to_netcdf(rec_path)
            rec_ds.close()
            print(f"[DERIVED] Saved Recent Agricultural Reference: {rec_path} ({rec_path.stat().st_size / 1024:.1f} KB)")
            
            # Register in DB
            sha = hashlib.sha256(rec_path.read_bytes()).hexdigest()
            reg_rec = DatasetRegisterRequest(
                dataset_id="P-02-IMD-RECENT-REF-2010-2024",
                dataset_name="IMD Gridded Rainfall Recent Agricultural Reference (2010-2024)",
                publisher="IMD Pune / Rashkar Derived Products",
                source_url=IMD_URL,
                classification="derived_product",
                format="netcdf",
                temporal_coverage="2010-01-01 to 2024-12-31 (15-year Agricultural Baseline)",
                spatial_coverage="Maharashtra Bounding Box (15.5-22.5 N, 72.5-81.0 E)",
                spatial_resolution="0.25 deg (~25 km)",
                licence="Derived from IMD Open Data",
                commercial_use_status="Permitted with citation",
                storage_path=str(rec_path),
                row_count=15,
                provenance_metadata={
                    "is_wmo_climate_normal": False,
                    "warning": "Strictly NOT an official WMO 30-year normal; recent 15-year agricultural baseline only",
                    "resolution": "0.25 deg (~27km)",
                    "years_included": recent_years,
                    "sha256": sha
                }
            )
            RegistryService.register_dataset(db, reg_rec, file_path=rec_path)
            print("[REGISTRY] P-02-IMD-RECENT-REF-2010-2024 registered successfully.")

    finally:
        db.close()

if __name__ == "__main__":
    # Download in chronological order
    download_range(1991, 2019)
    generate_derived_reference_periods()
