import sys
from pathlib import Path
import httpx
import pandas as pd
from data_pipeline.download_utils import compute_sha256
from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.core.config import settings

def acquire_mirca_calendar() -> Path:
    """
    Download MIRCA-OS 2020 crop calendar CSV from HydroShare,
    filter for India / Maharashtra bounding box (Lat 15.5-22.5 N, Lon 72.5-81.0 E),
    save raw + cleaned version, compute SHA-256, and register.
    """
    raw_dir = settings.RAW_DATA_DIR / "CROP_CALENDARS" / "MIRCA_OS"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "MIRCA-OS_2020_rf_v2.csv"
    clean_dir = settings.PROCESSED_DATA_DIR / "CROP_CALENDARS"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_file = clean_dir / "mirca_os_maharashtra_calendar.csv"

    url = "https://www.hydroshare.org/resource/e4582ca0042148338bb5e0148b749ed6/data/contents/Crop%20Calendar/MIRCA-OS_2020_rf_v2.csv"

    if not raw_file.exists():
        print(f"Downloading MIRCA-OS 2020 Rainfed Crop Calendar from HydroShare...")
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(raw_file, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
        print(f"Saved raw MIRCA-OS to {raw_file} ({raw_file.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"Raw MIRCA-OS file already exists at {raw_file}")

    raw_checksum = compute_sha256(raw_file)

    # Inspect columns
    print("Inspecting MIRCA-OS columns and filtering for Maharashtra region...")
    df = pd.read_csv(raw_file, encoding="latin-1")
    print("Columns:", list(df.columns))
    print(f"Total global grid cells: {len(df)}")

    # Filter for Maharashtra
    maha_mask = (df["Country"].str.lower() == "india") & (df["State"].str.lower() == "maharashtra")
    df_maha = df[maha_mask]
    print(f"Filtered {len(df_maha)} crop calendar records for Maharashtra.")
    df_maha.to_csv(clean_file, index=False)

    clean_checksum = compute_sha256(clean_file)

    # Register in DB
    db = SessionLocal()
    try:
        reg = DatasetRegisterRequest(
            dataset_id="Y-07-MIRCA-OS-2020",
            dataset_name="MIRCA-OS Global Crop Calendar 2020 (Rainfed)",
            publisher="Nature Scientific Data / HydroShare",
            source_url="https://hydroshare.org/resource/e4582ca0042148338bb5e0148b749ed6/",
            classification="direct_download",
            format="csv",
            temporal_coverage="2020 Benchmark",
            spatial_coverage="Global (Filtered to Maharashtra)",
            spatial_resolution="5 arc-minute (~10 km)",
            licence="Creative Commons Attribution 4.0 International (CC BY 4.0)",
            commercial_use_status="Permitted with attribution",
            storage_path=str(clean_file),
            row_count=len(df_maha),
            provenance_metadata={
                "raw_file": str(raw_file),
                "raw_sha256": raw_checksum,
                "clean_sha256": clean_checksum,
                "citation": "A global open-source dataset of monthly irrigated and rainfed cropped areas (MIRCA-OS)"
            }
        )
        record = RegistryService.register_dataset(db, reg, file_path=clean_file)
        print(f"Registered {record.dataset_id} in dataset registry successfully.")
    finally:
        db.close()

    return clean_file

if __name__ == "__main__":
    acquire_mirca_calendar()
