"""
CropNet AI — Non-Crop Production Data Integrity Verification Script.

Bitwise comparison of all non-crop tables between the pre-deployment backup (rev 004)
and the live Supabase production database (rev 005) to prove 100% data preservation.
"""
import sys
import json
import hashlib
import datetime
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
_CROPNET_ROOT = _SCRIPT_DIR.parents[1]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text
from cropnet.services.api.app.core.config import settings

BACKUP_JSON_PATH = _SCRIPT_DIR / "backups/supabase_backup_rev004_20261106_211652.json"
NON_CROP_TABLES = [
    "farms",
    "farm_weather_snapshots",
    "farm_climate_summaries",
    "farm_soil_profiles",
    "soil_parameters"
]


def canonical_json_hash(rows):
    """Compute deterministic SHA256 hash of a list of row dicts."""
    canonical_str = json.dumps(rows, sort_keys=True, default=str)
    return hashlib.sha256(canonical_str.encode("utf-8")).hexdigest()


def verify_non_crop_data_integrity():
    print("=" * 78)
    print("  CROPNET AI — NON-CROP PRODUCTION DATA INTEGRITY VERIFICATION")
    print("=" * 78)

    assert BACKUP_JSON_PATH.exists(), f"Backup file not found: {BACKUP_JSON_PATH}"
    with open(BACKUP_JSON_PATH, "r", encoding="utf-8") as f:
        backup = json.load(f)

    url = settings.SYNC_DATABASE_URL
    assert url, "SYNC_DATABASE_URL not configured."
    engine = create_engine(url)

    all_matched = True

    with engine.connect() as conn:
        for tbl in NON_CROP_TABLES:
            print(f"\nAuditing table: '{tbl}'...")

            # 1. Fetch backup rows
            backup_rows = backup["tables"][tbl]["rows"]
            # Sort deterministically by primary key 'id'
            backup_rows.sort(key=lambda r: r.get("id", ""))
            backup_hash = canonical_json_hash(backup_rows)
            backup_count = len(backup_rows)

            # 2. Fetch current production rows
            db_rows_raw = conn.execute(text(f'SELECT * FROM "{tbl}" ORDER BY id;')).mappings().all()
            current_rows = []
            for r in db_rows_raw:
                d = dict(r)
                for k, v in d.items():
                    if isinstance(v, (datetime.datetime, datetime.date)):
                        d[k] = v.isoformat()
                current_rows.append(d)

            current_hash = canonical_json_hash(current_rows)
            current_count = len(current_rows)

            print(f"  - Backup row count:  {backup_count}")
            print(f"  - Current row count: {current_count}")
            print(f"  - Backup SHA256:     {backup_hash}")
            print(f"  - Current SHA256:    {current_hash}")

            assert backup_count == current_count, f"Row count mismatch in table '{tbl}'!"
            assert backup_hash == current_hash, f"Data content mismatch in table '{tbl}'!"

            # Field by field verification
            for i, (b_row, c_row) in enumerate(zip(backup_rows, current_rows)):
                assert b_row == c_row, f"Row mismatch in '{tbl}' at index {i}:\nBackup: {b_row}\nCurrent: {c_row}"

            print(f"  --> MATCH CONFIRMED: Table '{tbl}' has 100% bitwise data identity with pre-migration backup.")

    print("\n" + "=" * 78)
    print("  ALL NON-CROP PRODUCTION TABLES REMAIN 100% UNCHANGED AND UNMODIFIED!")
    print("=" * 78)
    return True


if __name__ == "__main__":
    verify_non_crop_data_integrity()
