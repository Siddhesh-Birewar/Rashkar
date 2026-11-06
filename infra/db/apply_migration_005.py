"""
CropNet AI — Apply Migration 005 to Supabase Database.

Executes only migration 005_evidence_provenance_updates using Alembic.
Strictly non-destructive; preserves all existing crop, farm, and user records.
"""
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_CROPNET_ROOT = _SCRIPT_DIR.parents[1]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from cropnet.services.api.app.core.config import settings


def apply_migration_005():
    url = settings.SYNC_DATABASE_URL
    if not url:
        raise RuntimeError("SYNC_DATABASE_URL is not configured.")

    engine = create_engine(url)
    with engine.connect() as conn:
        current_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"Current Alembic revision before upgrade: {current_rev}")
        if current_rev != "004_add_crop_knowledge":
            raise RuntimeError(
                f"Cannot apply migration 005: Expected revision '004_add_crop_knowledge', found '{current_rev}'"
            )

    alembic_ini_path = _SCRIPT_DIR / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("script_location", str(_SCRIPT_DIR / "migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", url)

    print("Applying migration: 004_add_crop_knowledge -> 005_evidence_provenance_updates...")
    command.upgrade(alembic_cfg, "005_evidence_provenance_updates")

    with engine.connect() as conn:
        new_rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"Alembic revision after upgrade: {new_rev}")
        if new_rev != "005_evidence_provenance_updates":
            raise RuntimeError(f"Upgrade failed: Expected revision '005_evidence_provenance_updates', got '{new_rev}'")

    print("\nMigration 005 applied successfully to Supabase database!")
    return True


if __name__ == "__main__":
    apply_migration_005()
