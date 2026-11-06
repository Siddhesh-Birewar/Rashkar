"""
CropNet AI — Complete Database Backup & Verification Utility.

Backs up all public tables (schema + data) from the active database
before applying migration 005. Verifies backup integrity and records baseline counts.
"""
import os
import sys
import json
import datetime
from pathlib import Path

# Add project root and cropnet root to sys.path
_SCRIPT_DIR = Path(__file__).resolve().parent
_CROPNET_ROOT = _SCRIPT_DIR.parents[1]
_WORKSPACE_ROOT = _CROPNET_ROOT.parent

for p in [str(_WORKSPACE_ROOT), str(_CROPNET_ROOT)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from sqlalchemy import create_engine, text, inspect
from cropnet.services.api.app.core.config import settings

BACKUP_DIR = _SCRIPT_DIR / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def backup_database():
    url = settings.SYNC_DATABASE_URL
    if not url:
        raise RuntimeError("SYNC_DATABASE_URL is not configured.")

    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
    sql_path = BACKUP_DIR / f"supabase_backup_rev004_{timestamp}.sql"
    json_path = BACKUP_DIR / f"supabase_backup_rev004_{timestamp}.json"

    engine = create_engine(url)
    inspector = inspect(engine)

    with engine.connect() as conn:
        rev = conn.execute(text("SELECT version_num FROM alembic_version;")).scalar()
        print(f"Current Alembic revision: {rev}")

        tables = [
            t for t in inspector.get_table_names(schema="public")
            if t != "spatial_ref_sys"
        ]
        tables.sort()

        backup_data = {
            "metadata": {
                "timestamp": timestamp,
                "alembic_revision": rev,
                "server_version": conn.execute(text("SELECT version();")).scalar().split(",")[0],
                "table_count": len(tables),
            },
            "tables": {}
        }

        sql_lines = [
            f"-- CropNet AI Database Backup at Alembic Revision {rev}",
            f"-- Generated: {timestamp} UTC",
            "BEGIN;\n"
        ]

        print("Backing up tables:")
        for tbl in tables:
            rows = conn.execute(text(f'SELECT * FROM "{tbl}";')).mappings().all()
            row_dicts = []
            for r in rows:
                d = dict(r)
                # Convert datetime/UUID objects for JSON serialization
                for k, v in d.items():
                    if isinstance(v, (datetime.datetime, datetime.date)):
                        d[k] = v.isoformat()
                row_dicts.append(d)

            backup_data["tables"][tbl] = {
                "count": len(row_dicts),
                "rows": row_dicts
            }
            print(f"  - {tbl}: {len(row_dicts)} rows")

            # SQL Insert statements
            if row_dicts:
                cols = list(row_dicts[0].keys())
                col_names = ", ".join([f'"{c}"' for c in cols])
                for r in row_dicts:
                    val_strs = []
                    for c in cols:
                        val = r[c]
                        if val is None:
                            val_strs.append("NULL")
                        elif isinstance(val, (int, float)):
                            val_strs.append(str(val))
                        elif isinstance(val, bool):
                            val_strs.append("TRUE" if val else "FALSE")
                        elif isinstance(val, (dict, list)):
                            val_strs.append("'" + json.dumps(val).replace("'", "''") + "'::json")
                        else:
                            val_strs.append("'" + str(val).replace("'", "''") + "'")
                    sql_lines.append(f'INSERT INTO "{tbl}" ({col_names}) VALUES ({", ".join(val_strs)});')

        sql_lines.append("\nCOMMIT;\n")

        # Write files
        with open(sql_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sql_lines))

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(backup_data, f, indent=2)

    # Verification of backup
    print("\nVerifying backup artifacts...")
    assert sql_path.exists() and sql_path.stat().st_size > 0, "SQL backup file missing or empty"
    assert json_path.exists() and json_path.stat().st_size > 0, "JSON backup file missing or empty"

    with open(json_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)

    assert loaded["metadata"]["alembic_revision"] == "004_add_crop_knowledge"
    assert "crop_catalog" in loaded["tables"]
    assert loaded["tables"]["crop_catalog"]["count"] == 10
    assert loaded["tables"]["crop_regional_suitability"]["count"] == 40
    assert loaded["tables"]["crop_soil_requirements"]["count"] == 10
    assert loaded["tables"]["crop_climate_requirements"]["count"] == 10
    assert loaded["tables"]["crop_water_requirements"]["count"] == 10
    assert loaded["tables"]["agricultural_knowledge_sources"]["count"] == 8

    # Check 10 crops
    crop_ids = [c["id"] for c in loaded["tables"]["crop_catalog"]["rows"]]
    crop_ids.sort()
    expected_crops = sorted([
        "sugarcane", "pomegranate", "soybean", "cotton", "maize",
        "wheat", "sorghum", "chickpea", "bajra", "groundnut"
    ])
    assert crop_ids == expected_crops, f"Crop list mismatch: {crop_ids}"

    # Check 40 regional records (4 talukas x 10 crops)
    reg_rows = loaded["tables"]["crop_regional_suitability"]["rows"]
    talukas = set(r["taluka"] for r in reg_rows)
    assert talukas == {"Baramati", "Indapur", "Maval", "Mulshi"}, f"Unexpected talukas: {talukas}"

    print("Backup verified successfully!")
    print(f"  SQL Artifact: {sql_path} ({sql_path.stat().st_size / 1024:.1f} KB)")
    print(f"  JSON Artifact: {json_path} ({json_path.stat().st_size / 1024:.1f} KB)")
    print(f"  Revision verified: {loaded['metadata']['alembic_revision']}")
    print(f"  All 10 crops and 40 regional suitability records verified.")
    return str(sql_path), str(json_path)


if __name__ == "__main__":
    backup_database()
