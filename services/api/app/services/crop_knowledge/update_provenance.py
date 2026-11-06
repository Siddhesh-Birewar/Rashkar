"""
Safe, idempotent database provenance update script for Phase 4.1.

Applies verified agricultural corrections:
- Pomegranate: pH 6.5-7.0 (optimum), 8.5 (tolerable max), None (tolerable min, unverified)
- Chickpea: pH 6.0-8.0, 35C thermal max, separate ICRISAT and MPKV irrigation statements
- Provenance status flags: verified_authoritative, derived, regional_screening, requires_regional_validation
- Daily tree water table (L/tree/day) for pomegranate

Usage:
    python update_provenance.py [--dry-run]
"""
import sys
from pathlib import Path

# Add project root and cropnet root to sys.path so cropnet imports resolve seamlessly
_CROP_FEATURE_DIR = Path(__file__).resolve().parents[6]
_CROPNET_DIR = Path(__file__).resolve().parents[5]
for p in [str(_CROP_FEATURE_DIR), str(_CROPNET_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import argparse
import logging
from typing import Dict, Any

from sqlalchemy import text
from cropnet.services.api.app.core.database import SessionLocal, engine
from cropnet.services.api.app.services.crop_knowledge.crop_service import CropKnowledgeService
from cropnet.services.api.app.services.crop_knowledge.seed_data import KNOWLEDGE_SOURCES, CROPS_DATA

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("update_provenance")


def report_expected_changes():
    """Print the exact changes to be executed."""
    logger.info("=== Phase 4.1 Expected Database Updates ===")
    logger.info("1. Schema Alterations (Non-destructive, backward compatible):")
    logger.info("   - crop_soil_requirements: ALTER COLUMN ph_tolerable_min DROP NOT NULL")
    logger.info("   - crop_soil_requirements: ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50)")
    logger.info("   - crop_soil_requirements: ADD COLUMN IF NOT EXISTS unverified_parameters JSON")
    logger.info("   - crop_climate_requirements: ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50)")
    logger.info("   - crop_water_requirements: ALTER COLUMN annual_water_requirement_mm_min DROP NOT NULL")
    logger.info("   - crop_water_requirements: ALTER COLUMN annual_water_requirement_mm_max DROP NOT NULL")
    logger.info("   - crop_water_requirements: ADD COLUMN IF NOT EXISTS daily_water_table JSON")
    logger.info("   - crop_water_requirements: ADD COLUMN IF NOT EXISTS irrigation_stages_detail JSON")
    logger.info("   - crop_water_requirements: ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50)")
    logger.info("   - crop_regional_suitability: ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50)")
    logger.info("2. Knowledge Sources: Upsert 4 newly verified sources, reclassify historical bibliographic sources.")
    logger.info("3. Pomegranate: Correct pH (6.5-7.0 / max 8.5 / min None), add daily water table (480 entries across 3 Bahars), set Maval/Mulshi to requires_regional_validation.")
    logger.info("4. Chickpea: Correct pH (6.0-8.0 / min None), add ph_context_notes and best_suited_soil_textures (deep loams/silty clay loams), reproductive-stage thermal max (35C) without pollen sterility claim, decouple irrigation into ICRISAT & MPKV statements.")
    logger.info("5. Regional Suitability: Update evidence_status across all 40 records (4 pilot talukas x 10 crops).")
    logger.info("===========================================")


def apply_provenance_schema_updates(db) -> None:
    """Safely apply DDL statements idempotently."""
    ddl_statements = [
        # Soil
        "ALTER TABLE crop_soil_requirements ALTER COLUMN ph_tolerable_min DROP NOT NULL;",
        "ALTER TABLE crop_soil_requirements ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50) DEFAULT 'derived';",
        "ALTER TABLE crop_soil_requirements ADD COLUMN IF NOT EXISTS unverified_parameters JSONB;",
        "ALTER TABLE crop_soil_requirements ADD COLUMN IF NOT EXISTS ph_context_notes TEXT;",
        "ALTER TABLE crop_soil_requirements ADD COLUMN IF NOT EXISTS best_suited_soil_textures JSONB;",
        # Climate
        "ALTER TABLE crop_climate_requirements ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50) DEFAULT 'derived';",
        "ALTER TABLE crop_climate_requirements ADD COLUMN IF NOT EXISTS thermal_threshold_context TEXT;",
        # Water
        "ALTER TABLE crop_water_requirements ALTER COLUMN annual_water_requirement_mm_min DROP NOT NULL;",
        "ALTER TABLE crop_water_requirements ALTER COLUMN annual_water_requirement_mm_max DROP NOT NULL;",
        "ALTER TABLE crop_water_requirements ADD COLUMN IF NOT EXISTS daily_water_table JSONB;",
        "ALTER TABLE crop_water_requirements ADD COLUMN IF NOT EXISTS irrigation_stages_detail JSONB;",
        "ALTER TABLE crop_water_requirements ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50) DEFAULT 'derived';",
        # Regional
        "ALTER TABLE crop_regional_suitability ADD COLUMN IF NOT EXISTS evidence_status VARCHAR(50) DEFAULT 'regional_screening';"
    ]

    for stmt in ddl_statements:
        try:
            db.execute(text(stmt))
            db.commit()
            logger.info("Executed: %s", stmt)
        except Exception as e:
            db.rollback()
            # If SQLite or non-Postgres dialect, handle accordingly
            logger.warning("Statement '%s' skipped or handled: %s", stmt, e)


def execute_update(dry_run: bool = False):
    report_expected_changes()
    if dry_run:
        logger.info("[DRY RUN] No database changes executed.")
        return

    db = SessionLocal()
    try:
        logger.info("Applying schema modifications...")
        apply_provenance_schema_updates(db)

        logger.info("Applying verified seed data corrections...")
        svc = CropKnowledgeService()
        count = svc.seed_knowledge_base(db)
        logger.info("Successfully updated %d crops with Phase 4.1 provenance and corrections.", count)
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CropNet Phase 4.1 Provenance Update")
    parser.add_argument("--dry-run", action="store_true", help="Report planned changes without modifying database")
    args = parser.parse_args()
    execute_update(dry_run=args.dry_run)
