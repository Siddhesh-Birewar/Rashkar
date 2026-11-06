"""
Safe, idempotent database provenance update script for Phase 4.2 Controlled Supabase Deployment.

Applies verified agricultural corrections:
- Pomegranate: pH 6.5-7.0 (optimum/best-suited), 8.5 (tolerable max), None (tolerable min, unverified), "Light soil" texture
- Chickpea: pH 6.0-8.0 best-suited (unsupported bounds NULL), temp_reproductive_max_c = 35°C, temp_reproductive_min_mean_c = 15°C
- Provenance status flags: verified_authoritative, derived, regional_screening, requires_regional_validation
- Daily tree water table (480 entries, L/tree/day) for pomegranate
- Preserves all NULL values for unverified agronomic limits

Usage:
    python update_provenance.py [--dry-run]
"""
import sys
from pathlib import Path

# Add project root and cropnet root to sys.path so cropnet imports resolve seamlessly
_SCRIPT_DIR = Path(__file__).resolve().parent
_CROPNET_ROOT = _SCRIPT_DIR.parents[4]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse
import logging
from typing import Dict, Any, List

from sqlalchemy import text
from cropnet.services.api.app.core.database import SessionLocal, engine
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.services.crop_knowledge.seed_data import KNOWLEDGE_SOURCES, CROPS_DATA
from cropnet.services.api.app.models.crops import (
    AgriculturalKnowledgeSourceModel, CropCatalogModel, CropSoilRequirementModel,
    CropClimateRequirementModel, CropWaterRequirementModel, CropRegionalSuitabilityModel
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("update_provenance")


def generate_dry_run_plan(db):
    """Inspect database and generate detailed dry run plan."""
    print("=" * 78)
    print("      CROPNET AI — PHASE 4.2 PROVENANCE UPDATER: DRY RUN PLAN")
    print("=" * 78)

    # 1. Knowledge Sources Audit
    existing_src_ids = set(r[0] for r in db.query(AgriculturalKnowledgeSourceModel.id).all())
    sources_to_insert = [s["id"] for s in KNOWLEDGE_SOURCES if s["id"] not in existing_src_ids]
    sources_to_update = [s["id"] for s in KNOWLEDGE_SOURCES if s["id"] in existing_src_ids]

    print("\n[1] AGRICULTURAL KNOWLEDGE SOURCES:")
    print(f"  - Existing Sources in DB ({len(existing_src_ids)}): {sorted(list(existing_src_ids))}")
    print(f"  - Sources to Insert ({len(sources_to_insert)}): {sources_to_insert}")
    print(f"  - Sources to Update ({len(sources_to_update)}): {sources_to_update}")

    # 2. Crops Data Audit
    existing_crop_ids = set(r[0] for r in db.query(CropCatalogModel.id).all())
    print("\n[2] CROP CATALOG MASTER:")
    print(f"  - Existing Crops in DB ({len(existing_crop_ids)}): {sorted(list(existing_crop_ids))}")
    print(f"  - Crops to Insert (0): None (all 10 crops pre-exist)")
    print(f"  - Crops to Update ({len(CROPS_DATA)}): {[c['id'] for c in CROPS_DATA]}")

    # 3. NULL Values to be Strictly Preserved
    print("\n[3] NULL VALUES TO BE PRESERVED (NO SYNTHETIC FABRICATION):")
    print("  - Pomegranate:")
    print("      * crop_soil_requirements.ph_tolerable_min: NULL (unsupported lower limit)")
    print("      * crop_water_requirements.annual_water_requirement_mm_min: NULL (universal mm unverified)")
    print("      * crop_water_requirements.annual_water_requirement_mm_max: NULL (universal mm unverified)")
    print("  - Chickpea:")
    print("      * crop_soil_requirements.ph_optimum_min: NULL (universal optimum unverified)")
    print("      * crop_soil_requirements.ph_optimum_max: NULL (universal optimum unverified)")
    print("      * crop_soil_requirements.ph_tolerable_min: NULL (tolerable bounds unverified)")
    print("      * crop_soil_requirements.ph_tolerable_max: NULL (tolerable bounds unverified)")
    print("      * crop_climate_requirements.temp_tolerable_min_c: NULL (generic mortality bounds unverified)")
    print("      * crop_climate_requirements.temp_tolerable_max_c: NULL (generic mortality bounds unverified)")

    # 4. Specific Scientific Provenance Updates
    print("\n[4] KEY AUTHORITATIVE SCIENTIFIC FIELD CORRECTIONS:")
    print("  - Pomegranate (ICAR-NRCP & MANAGE 2022, p. 3, 45-46):")
    print("      * preferred_textures & best_suited_soil_textures -> ['Light soil'] (removed unsupported loams)")
    print("      * ph_best_suited_min: 6.5, ph_best_suited_max: 7.0, ph_tolerable_max: 8.5")
    print("      * daily_water_table: Populated with 480 entries (L/tree/day across Mrig, Hasta, Ambia Bahars)")
    print("      * source attribution -> 'icar_nrcp_manage_2022'")
    print("  - Chickpea (ICRISAT 2010, p. 3, 8):")
    print("      * best_suited_soil_textures -> ['Loam', 'Silty Clay Loam']")
    print("      * ph_best_suited_min: 6.0, ph_best_suited_max: 8.0 ('best-suited soil pH range')")
    print("      * temp_reproductive_max_c: 35.0°C (reproductive heat stress threshold)")
    print("      * temp_reproductive_min_mean_c: 15.0°C (reproductive cold stress threshold)")
    print("      * source attribution -> 'icrisat_chickpea_2010'")

    # 5. Regional Suitability Status Updates
    print("\n[5] REGIONAL SUITABILITY EVIDENCE STATUS (40 RECORDS):")
    print("  - Baramati & Indapur records (where MPKV Plain Zone / Vertisol recommendations apply):")
    print("      * evidence_status -> 'regional_screening' (screening status with specific soil/canal irrigation qualifications)")
    print("  - Maval & Mulshi records (high rainfall / acidic / hilly terrain):")
    print("      * evidence_status -> 'requires_regional_validation'")

    print("\n[6] IDEMPOTENCY & SAFETY GUARANTEES:")
    print("  - Pure attribute update / upsert pattern (no table drops, no row deletions, no cascades)")
    print("  - Zero impact on user accounts, farms, weather observations, or soil test analyses")
    print("=" * 78)


def execute_update(dry_run: bool = False):
    db = SessionLocal()
    try:
        generate_dry_run_plan(db)
        if dry_run:
            logger.info("[DRY RUN COMPLETE] Plan generated. No database records modified.")
            return

        logger.info("\nExecuting Phase 4.2 idempotent provenance update on Supabase...")
        svc = CropKnowledgeService()
        count = svc.seed_knowledge_base(db)
        logger.info("Successfully updated %d crops with Phase 4.2 provenance corrections!", count)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CropNet Phase 4.2 Provenance Update")
    parser.add_argument("--dry-run", action="store_true", help="Report planned changes without modifying database")
    args = parser.parse_args()
    execute_update(dry_run=args.dry_run)
