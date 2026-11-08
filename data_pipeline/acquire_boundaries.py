import json
from pathlib import Path
import httpx
from data_pipeline.download_utils import compute_sha256
from backend.app.db.session import SessionLocal
from backend.app.services.registry_service import RegistryService
from backend.app.schemas.registry import DatasetRegisterRequest
from backend.app.core.config import settings

def acquire_maharashtra_boundaries() -> Path:
    """
    Download India district boundaries GeoJSON, filter specifically for Maharashtra,
    store raw + clean standard version, compute SHA-256, and register.
    """
    raw_dir = settings.RAW_DATA_DIR / "GEO" / "BOUNDARIES"
    raw_dir.mkdir(parents=True, exist_ok=True)
    raw_file = raw_dir / "india_districts_raw.geojson"
    clean_dir = settings.PROCESSED_DATA_DIR / "GEO"
    clean_dir.mkdir(parents=True, exist_ok=True)
    clean_file = clean_dir / "maharashtra_districts.geojson"

    url = "https://raw.githubusercontent.com/geohacker/india/master/district/india_district.geojson"

    if not raw_file.exists():
        print(f"Downloading India district boundaries GeoJSON from {url}...")
        with httpx.Client(timeout=120.0, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            with open(raw_file, "wb") as f:
                f.write(resp.content)
        print(f"Raw file saved to {raw_file} ({raw_file.stat().st_size / (1024*1024):.2f} MB)")
    else:
        print(f"Raw boundaries file already exists at {raw_file}")

    raw_checksum = compute_sha256(raw_file)

    # Filter for Maharashtra districts
    print("Filtering GeoJSON features for Maharashtra...")
    with open(raw_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    maha_features = []
    for feat in data.get("features", []):
        props = feat.get("properties", {})
        # Check state name variants
        state = props.get("NAME_1") or props.get("state") or props.get("STATE") or props.get("State") or ""
        if "maharashtra" in state.lower():
            maha_features.append(feat)

    print(f"Found {len(maha_features)} Maharashtra district features.")

    maha_geojson = {
        "type": "FeatureCollection",
        "name": "maharashtra_districts",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": maha_features
    }

    with open(clean_file, "w", encoding="utf-8") as f:
        json.dump(maha_geojson, f, indent=2)

    clean_checksum = compute_sha256(clean_file)
    print(f"Cleaned Maharashtra GeoJSON saved to {clean_file}")
    print(f"Clean Checksum: {clean_checksum}")

    # Register in DB
    db = SessionLocal()
    try:
        reg = DatasetRegisterRequest(
            dataset_id="S-05-MAHA-BOUNDARIES",
            dataset_name="Maharashtra District Administrative Boundaries GeoJSON",
            publisher="Survey of India / OpenData Community (Geohacker)",
            source_url=url,
            classification="direct_download",
            format="geojson",
            temporal_coverage="Census 2011 / Current",
            spatial_coverage="Maharashtra (All 36 Districts)",
            spatial_resolution="Polygon Boundaries",
            licence="Open Data Commons Open Database License (ODbL)",
            commercial_use_status="Permitted with attribution",
            storage_path=str(clean_file),
            row_count=len(maha_features),
            provenance_metadata={
                "raw_file": str(raw_file),
                "raw_sha256": raw_checksum,
                "clean_sha256": clean_checksum,
                "feature_count": len(maha_features)
            }
        )
        record = RegistryService.register_dataset(db, reg, file_path=clean_file)
        print(f"Registered {record.dataset_id} in dataset registry.")
    finally:
        db.close()

    return clean_file

if __name__ == "__main__":
    acquire_maharashtra_boundaries()
