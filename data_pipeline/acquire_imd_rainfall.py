import sys
from pathlib import Path
import httpx
import xarray as xr
from data_pipeline.download_utils import compute_sha256
from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.core.config import settings

def acquire_imd_rainfall_year(year: int = 2024) -> Path:
    """
    Download genuine IMD 0.25 degree daily gridded rainfall NetCDF from IMD Pune.
    Computes SHA-256 and registers in Rashkar dataset registry.
    """
    url = "https://imdpune.gov.in/cmpg/Griddata/RF25.php"
    dest_dir = settings.RAW_DATA_DIR / "WEATHER" / "IMD_RAINFALL"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"ind{year}_rfp25.nc"

    if dest_file.exists() and dest_file.stat().st_size > 1000000:
        print(f"File {dest_file.name} already exists ({dest_file.stat().st_size / (1024*1024):.2f} MB). Skipping network download.")
    else:
        print(f"Requesting IMD 0.25° Daily Rainfall NetCDF for {year} from {url}...")
        with httpx.Client(timeout=120.0, verify=False) as client:
            response = client.post(url, data={"RF25": str(year)})
            response.raise_for_status()
            with open(dest_file, "wb") as f:
                f.write(response.content)

    file_size_mb = dest_file.stat().st_size / (1024 * 1024)
    checksum = compute_sha256(dest_file)
    print(f"Successfully downloaded {dest_file.name} ({file_size_mb:.2f} MB)")
    print(f"SHA-256 Checksum: {checksum}")

    # Inspect with xarray
    ds = xr.open_dataset(dest_file)
    print("NetCDF Dimensions:", dict(ds.dims))
    print("NetCDF Data Variables:", list(ds.data_vars.keys()))
    lat_coord = ds["LATITUDE"] if "LATITUDE" in ds else ds.lat
    lon_coord = ds["LONGITUDE"] if "LONGITUDE" in ds else ds.lon
    print("Spatial bounds: lat", float(lat_coord.min()), "to", float(lat_coord.max()),
          "| lon", float(lon_coord.min()), "to", float(lon_coord.max()))
    ds.close()

    # Register in database
    db = SessionLocal()
    try:
        reg_request = DatasetRegisterRequest(
            dataset_id=f"S-03-IMD-RAIN-{year}",
            dataset_name=f"IMD 0.25° Daily Gridded Rainfall {year}",
            publisher="Climate Research and Services, IMD Pune",
            source_url="https://imdpune.gov.in/cmpg/Griddata/Rainfall_25_NetCDF.html",
            classification="direct_download",
            format="netcdf",
            temporal_coverage=str(year),
            spatial_coverage="India (0.25 degree)",
            spatial_resolution="0.25 deg (~25 km)",
            licence="Government of India / IMD Open Data",
            commercial_use_status="Permitted with citation",
            storage_path=str(dest_file),
            row_count=366 if (year % 4 == 0) else 365,
            provenance_metadata={
                "variable_name": "RAINFALL",
                "unit": "mm/day",
                "source_grid": "IMD 0.25 x 0.25"
            }
        )
        record = RegistryService.register_dataset(db, reg_request, file_path=dest_file)
        print(f"Registered {record.dataset_id} in dataset_registry successfully!")
    finally:
        db.close()

    return dest_file

if __name__ == "__main__":
    acquire_imd_rainfall_year(2024)
