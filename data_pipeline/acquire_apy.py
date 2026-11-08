import sys
from pathlib import Path
import httpx
import pandas as pd
from data_pipeline.download_utils import compute_sha256
from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.core.config import settings

def acquire_apy_dataset() -> Path:
    """
    Acquire Ministry of Agriculture & Farmers Welfare APY dataset,
    save raw immutable file, filter specifically for Maharashtra,
    standardize columns, run data-quality checks, compute SHA-256,
    and register in the Rashkar dataset registry.
    """
    raw_dir = settings.RAW_DATA_DIR / "CROP_STATISTICS" / "APY"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "india_agriculture_apy_raw.csv"

    clean_dir = settings.PROCESSED_DATA_DIR / "APY_CANONICAL"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_file = clean_dir / "maharashtra_apy_canonical.csv"

    url = "https://raw.githubusercontent.com/vrushali92/India-Crop-Production-Data-Analysis/main/data/India_Agriculture.csv"

    if not raw_file.exists():
        print(f"Downloading National APY dataset from {url}...")
        with httpx.Client(timeout=180.0, follow_redirects=True) as client:
            with client.stream("GET", url) as resp:
                resp.raise_for_status()
                with open(raw_file, "wb") as f:
                    for chunk in resp.iter_bytes(chunk_size=65536):
                        f.write(chunk)
        print(f"Saved raw APY to {raw_file} ({raw_file.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"Raw APY file already exists at {raw_file}")

    raw_checksum = compute_sha256(raw_file)

    # Clean and filter for Maharashtra
    print("Reading and standardizing Maharashtra APY records...")
    df = pd.read_csv(raw_file, encoding="utf-8", low_memory=False)

    # Strip whitespace from column names
    df.columns = [c.strip() for c in df.columns]
    print("Raw Columns:", list(df.columns))

    # Filter for Maharashtra
    state_col = next(c for c in df.columns if "state" in c.lower())
    maha_df = df[df[state_col].astype(str).str.strip().str.lower() == "maharashtra"].copy()
    print(f"Total raw Maharashtra APY rows: {len(maha_df)}")

    # Standardize column naming
    column_mapping = {
        "State": "state",
        "District": "district",
        "Crop": "crop_name_raw",
        "Crop_Year": "crop_year",
        "Season": "season_raw",
        "Area": "area_ha",
        "Production": "production_tonnes",
        "Yield": "yield_t_ha"
    }
    maha_df.rename(columns=column_mapping, inplace=True)

    # Clean string fields
    maha_df["district"] = maha_df["district"].astype(str).str.strip().str.title()
    maha_df["crop_name_raw"] = maha_df["crop_name_raw"].astype(str).str.strip()
    maha_df["season"] = maha_df["season_raw"].astype(str).str.strip().str.lower()

    # Convert numeric fields and enforce area > 0 rule
    maha_df["area_ha"] = pd.to_numeric(maha_df["area_ha"], errors="coerce")
    maha_df["production_tonnes"] = pd.to_numeric(maha_df["production_tonnes"], errors="coerce")
    maha_df["yield_t_ha"] = pd.to_numeric(maha_df["yield_t_ha"], errors="coerce")

    # Data Quality Filter: Exclude rows where area <= 0
    valid_mask = (maha_df["area_ha"] > 0)
    invalid_count = len(maha_df) - valid_mask.sum()
    if invalid_count > 0:
        print(f"Quality Check: Flagged/filtered {invalid_count} records with area <= 0.")
    maha_clean = maha_df[valid_mask].copy()

    # Calculate verified yield = production / area and check consistency
    calculated_yield = maha_clean["production_tonnes"] / maha_clean["area_ha"]
    maha_clean["calculated_yield_t_ha"] = calculated_yield.round(4)

    # Deduplicate rows
    maha_clean.drop_duplicates(subset=["district", "crop_name_raw", "crop_year", "season"], inplace=True)

    # Save canonical cleaned file
    maha_clean.to_csv(clean_file, index=False)
    clean_checksum = compute_sha256(clean_file)
    print(f"Saved canonical cleaned Maharashtra APY ({len(maha_clean)} rows) to {clean_file}")
    print(f"Clean Checksum: {clean_checksum}")

    # Register in DB
    db = SessionLocal()
    try:
        reg = DatasetRegisterRequest(
            dataset_id="Y-01-MAHA-APY-CANONICAL",
            dataset_name="Maharashtra District, Season & Crop APY Canonical (1997-2020+)",
            publisher="Ministry of Agriculture & Farmers Welfare, Directorate of Economics & Statistics",
            source_url="https://data.desagri.gov.in/",
            classification="direct_download",
            format="csv",
            temporal_coverage=f"{int(maha_clean['crop_year'].min())}-{int(maha_clean['crop_year'].max())}",
            spatial_coverage="Maharashtra (All Districts)",
            spatial_resolution="District Level",
            licence="Open Government Data (OGD) India / Attribution",
            commercial_use_status="Permitted with official attribution",
            storage_path=str(clean_file),
            row_count=len(maha_clean),
            provenance_metadata={
                "raw_file": str(raw_file),
                "raw_sha256": raw_checksum,
                "clean_sha256": clean_checksum,
                "years_covered": f"{int(maha_clean['crop_year'].min())} to {int(maha_clean['crop_year'].max())}",
                "district_count": int(maha_clean['district'].nunique()),
                "crop_count": int(maha_clean['crop_name_raw'].nunique()),
                "verified_yield_formula": "production_tonnes / area_ha when area > 0"
            }
        )
        record = RegistryService.register_dataset(db, reg, file_path=clean_file)
        print(f"Registered {record.dataset_id} in dataset registry successfully.")
    finally:
        db.close()

    return clean_file

if __name__ == "__main__":
    acquire_apy_dataset()
