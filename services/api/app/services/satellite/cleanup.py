"""
Synthetic Satellite QA Artifact Isolation and Cleanup Utilities.

Remediates Requirement R4:
- Identifies and isolates synthetic QA observations (e.g. S2B_MSIL2A_*T053649_N0500_R119_T43QDB)
  from farmer-facing dashboards while preserving authentic Sentinel-2 Level-2A observations.
- Purges or isolates synthetic 40x40 raster PNGs and mock JSON metadata from the derived raster cache.
"""
import os
import glob
import json
import logging
from typing import Optional, List
from sqlalchemy.orm import Session

from cropnet.services.api.app.models.satellite import SatelliteVegetationObservationModel
from cropnet.services.api.app.services.satellite.copernicus_client import DERIVED_RASTER_CACHE_DIR

logger = logging.getLogger(__name__)

SYNTHETIC_PRODUCT_PATTERN = "%T053649_N0500_R119_T43QDB"
SYNTHETIC_BARAMATI_FARM_ID = "94a1f16e-bf0d-4d3f-9bd3-d63a57189818"


def isolate_synthetic_database_observations(db: Session) -> int:
    """
    Isolates synthetic QA observation rows by setting quality_status to 'SYNTHETIC_QA_ISOLATED'.
    Leaves authentic Sentinel-2 Level-2A observations intact.

    Returns the count of rows isolated.
    """
    records = (
        db.query(SatelliteVegetationObservationModel)
        .filter(
            (SatelliteVegetationObservationModel.product_id.like(SYNTHETIC_PRODUCT_PATTERN))
            | (
                (SatelliteVegetationObservationModel.farm_id == SYNTHETIC_BARAMATI_FARM_ID)
                & (SatelliteVegetationObservationModel.total_pixel_count == 1521)
            )
        )
        .all()
    )

    count = 0
    for record in records:
        if record.quality_status != "SYNTHETIC_QA_ISOLATED":
            record.quality_status = "SYNTHETIC_QA_ISOLATED"
            record.quality_notes = (
                (record.quality_notes or "")
                + " [ISOLATED: Pre-Phase 6.2 synthetic QA simulation record isolated from production views]"
            ).strip()
            count += 1

    if count > 0:
        db.commit()
        logger.info("Isolated %d synthetic satellite QA observations in database.", count)

    return count


def cleanup_synthetic_filesystem_rasters(cache_dir: Optional[str] = None) -> List[str]:
    """
    Identifies and removes synthetic raster cache artifacts (e.g. 40x40 pixel grids and
    mock ESA product IDs) while preserving authentic clipped rasters.

    Returns the list of removed file paths.
    """
    target_dir = cache_dir or DERIVED_RASTER_CACHE_DIR
    if not os.path.isdir(target_dir):
        return []

    removed_files: List[str] = []

    # 1. Check for synthetic Baramati 40x40 raster artifacts
    pattern = os.path.join(target_dir, f"{SYNTHETIC_BARAMATI_FARM_ID}_*")
    for fpath in glob.glob(pattern):
        # Inspect metadata JSON if it's the synthetic 40x40 grid
        is_synthetic = False
        if fpath.endswith("_meta.json"):
            try:
                with open(fpath, "r") as mf:
                    data = json.load(mf)
                    if (
                        data.get("width") == 40
                        and data.get("height") == 40
                        and "T053649_N0500_R119_T43QDB" in data.get("product_id", "")
                    ):
                        is_synthetic = True
            except Exception:
                pass
        elif fpath.endswith(("_ndvi.png", "_ndmi.png", "_scl.png")):
            # If the matching meta.json is synthetic or if it matches the test fallback
            meta_json = os.path.join(target_dir, f"{SYNTHETIC_BARAMATI_FARM_ID}_meta.json")
            if os.path.exists(meta_json):
                try:
                    with open(meta_json, "r") as mf:
                        data = json.load(mf)
                        if data.get("width") == 40 and data.get("height") == 40:
                            is_synthetic = True
                except Exception:
                    pass

        if is_synthetic:
            try:
                os.remove(fpath)
                removed_files.append(fpath)
                logger.info("Removed synthetic raster artifact: %s", fpath)
            except OSError as e:
                logger.warning("Could not remove synthetic file %s: %s", fpath, e)

    return removed_files
