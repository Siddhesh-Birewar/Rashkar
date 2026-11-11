"""Alembic migration 010 tests: single head, upgrade from 009, schema drift, idempotency, downgrade."""

from pathlib import Path
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
import pytest
import sqlalchemy as sa

from cropnet.services.api.app.rashkar.models import (
    RashkarAdvisoryCatalogueModel,
    RashkarAgronomicThresholdModel,
    RashkarCanonicalCropModel,
    RashkarCropCycleModel,
    RashkarCropHeatLogModel,
    RashkarCropStageModel,
    RashkarFarmerResourceProfileModel,
    RashkarIncomeOpportunityModel,
    RashkarIncomeScenarioModel,
    RashkarSavedIncomePlanModel,
    RashkarWorkerHazardAuditLogModel,
    RashkarYieldAssessmentLogModel,
)


_REPO_ROOT = Path(__file__).resolve().parents[5]
_ALEMBIC_INI = _REPO_ROOT / "cropnet" / "infra" / "db" / "alembic.ini"
_MIGRATIONS_DIR = _REPO_ROOT / "cropnet" / "infra" / "db" / "migrations"

_RASHKAR_MODELS = (
    RashkarCanonicalCropModel,
    RashkarCropStageModel,
    RashkarAgronomicThresholdModel,
    RashkarAdvisoryCatalogueModel,
    RashkarIncomeOpportunityModel,
    RashkarCropCycleModel,
    RashkarWorkerHazardAuditLogModel,
    RashkarCropHeatLogModel,
    RashkarYieldAssessmentLogModel,
    RashkarFarmerResourceProfileModel,
    RashkarIncomeScenarioModel,
    RashkarSavedIncomePlanModel,
)

_RASHKAR_TABLE_NAMES = [m.__tablename__ for m in _RASHKAR_MODELS]


def _make_alembic_config(db_url: str) -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("script_location", str(_MIGRATIONS_DIR))
    cfg.set_main_option("sqlalchemy.url", db_url)
    return cfg


def _bootstrap_minimal_009_db(db_url: str) -> None:
    """Create minimal host prerequisite tables present at revision 009 (`farms`, `government_schemes`)."""
    engine = sa.create_engine(db_url)
    with engine.begin() as conn:
        conn.execute(
            sa.text(
                """
                CREATE TABLE farms (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    owner_id VARCHAR(36) NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    taluka VARCHAR(100) NOT NULL
                )
                """
            )
        )
        conn.execute(
            sa.text(
                """
                CREATE TABLE government_schemes (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    scheme_name VARCHAR(200) NOT NULL
                )
                """
            )
        )
    engine.dispose()


def test_alembic_head_is_010_and_chains_from_009():
    cfg = _make_alembic_config("sqlite:///:memory:")
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert heads == ["010_rashkar_tables"]
    rev = script.get_revision("010_rashkar_tables")
    assert rev is not None
    assert rev.down_revision == "009_government_schemes"


def test_upgrade_010_from_009_creates_all_12_tables_fks_and_matches_orms(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "rashkar_mig_upgrade.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    _bootstrap_minimal_009_db(db_url)
    cfg = _make_alembic_config(db_url)
    command.stamp(cfg, "009_government_schemes")
    command.upgrade(cfg, "010_rashkar_tables")

    engine = sa.create_engine(db_url)
    try:
        inspector = sa.inspect(engine)
        tables = set(inspector.get_table_names())
        assert "farms" in tables
        assert "government_schemes" in tables
        for tbl in _RASHKAR_TABLE_NAMES:
            assert tbl in tables, f"Missing migrated table: {tbl}"

        # Verify every ORM model column exists verbatim in the migrated schema
        for model_cls in _RASHKAR_MODELS:
            tbl_name = model_cls.__tablename__
            migrated_cols = {c["name"] for c in inspector.get_columns(tbl_name)}
            orm_cols = {c.name for c in model_cls.__table__.columns}
            missing = orm_cols - migrated_cols
            assert not missing, f"Table {tbl_name} missing ORM columns: {missing}"

        # Verify critical foreign key relationships
        stage_fks = inspector.get_foreign_keys("rashkar_crop_stages")
        assert any(
            fk["referred_table"] == "rashkar_canonical_crops"
            and fk["constrained_columns"] == ["crop_code"]
            for fk in stage_fks
        )
        cycle_fks = inspector.get_foreign_keys("rashkar_crop_cycles")
        assert any(
            fk["referred_table"] == "farms" and fk["constrained_columns"] == ["farm_id"]
            for fk in cycle_fks
        )
        scen_fks = inspector.get_foreign_keys("rashkar_income_scenarios")
        assert any(
            fk["referred_table"] == "farms" and fk["constrained_columns"] == ["farm_id"]
            for fk in scen_fks
        )
        assert any(
            fk["referred_table"] == "rashkar_income_opportunities"
            and fk["constrained_columns"] == ["opportunity_id"]
            for fk in scen_fks
        )
    finally:
        engine.dispose()


def test_upgrade_010_is_idempotent_when_tables_already_exist(tmp_path, monkeypatch):
    db_path = tmp_path / "rashkar_mig_idempotent.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    _bootstrap_minimal_009_db(db_url)
    cfg = _make_alembic_config(db_url)
    command.stamp(cfg, "009_government_schemes")
    command.upgrade(cfg, "010_rashkar_tables")

    # Re-stamp 009 with tables already present and upgrade again
    command.stamp(cfg, "009_government_schemes")
    command.upgrade(cfg, "010_rashkar_tables")

    engine = sa.create_engine(db_url)
    try:
        tables = set(sa.inspect(engine).get_table_names())
        for tbl in _RASHKAR_TABLE_NAMES:
            assert tbl in tables
    finally:
        engine.dispose()


def test_upgrade_010_detects_schema_drift(tmp_path, monkeypatch):
    db_path = tmp_path / "rashkar_mig_drift.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    _bootstrap_minimal_009_db(db_url)
    engine = sa.create_engine(db_url)
    with engine.begin() as conn:
        # Incomplete rashkar_crop_cycles missing `stage_source` and others
        conn.execute(
            sa.text(
                """
                CREATE TABLE rashkar_crop_cycles (
                    id VARCHAR(36) PRIMARY KEY NOT NULL,
                    farm_id VARCHAR(36) NOT NULL,
                    owner_id VARCHAR(36) NOT NULL,
                    crop_code VARCHAR(50) NOT NULL
                )
                """
            )
        )
    engine.dispose()

    cfg = _make_alembic_config(db_url)
    command.stamp(cfg, "009_government_schemes")
    with pytest.raises(RuntimeError, match="Schema drift detected in table 'rashkar_crop_cycles'"):
        command.upgrade(cfg, "010_rashkar_tables")


def test_downgrade_010_to_009_drops_rashkar_tables_and_preserves_host(
    tmp_path, monkeypatch
):
    db_path = tmp_path / "rashkar_mig_downgrade.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    _bootstrap_minimal_009_db(db_url)
    cfg = _make_alembic_config(db_url)
    command.stamp(cfg, "009_government_schemes")
    command.upgrade(cfg, "010_rashkar_tables")
    command.downgrade(cfg, "009_government_schemes")

    engine = sa.create_engine(db_url)
    try:
        tables = set(sa.inspect(engine).get_table_names())
        assert "farms" in tables
        assert "government_schemes" in tables
        for tbl in _RASHKAR_TABLE_NAMES:
            assert tbl not in tables, f"Table {tbl} remained after downgrade!"
    finally:
        engine.dispose()
