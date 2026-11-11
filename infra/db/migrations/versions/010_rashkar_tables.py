"""RASHKAR operational tables, reference catalogs, audit logs, and farm income plans

Revision ID: 010_rashkar_tables
Revises: 009_government_schemes
Create Date: 2026-11-11 20:00:00.000000

Adds the 12 strictly additive RASHKAR tables:
1. rashkar_canonical_crops
2. rashkar_crop_stages
3. rashkar_agronomic_thresholds
4. rashkar_advisory_catalogue
5. rashkar_income_opportunities
6. rashkar_crop_cycles
7. rashkar_worker_hazard_audit_logs
8. rashkar_crop_heat_logs
9. rashkar_yield_assessment_logs
10. rashkar_farmer_resource_profiles
11. rashkar_income_scenarios
12. rashkar_saved_income_plans

All migrations check for existing tables with schema-drift detection for idempotency
and apply guarded Supabase Row Level Security policies when the `auth` schema exists.
"""

from typing import Callable, Iterable, Sequence, Set, Union
from alembic import op
import sqlalchemy as sa


revision: str = "010_rashkar_tables"
down_revision: Union[str, None] = "009_government_schemes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_REFERENCE_TABLES: Sequence[str] = (
    "rashkar_canonical_crops",
    "rashkar_crop_stages",
    "rashkar_agronomic_thresholds",
    "rashkar_advisory_catalogue",
    "rashkar_income_opportunities",
)

_OWNER_SCOPED_TABLES: Sequence[str] = (
    "rashkar_crop_cycles",
    "rashkar_worker_hazard_audit_logs",
    "rashkar_crop_heat_logs",
    "rashkar_yield_assessment_logs",
    "rashkar_farmer_resource_profiles",
    "rashkar_income_scenarios",
    "rashkar_saved_income_plans",
)


def _auth_schema_exists(conn) -> bool:
    """True when running against a Supabase Postgres database (`auth` schema present)."""
    try:
        row = conn.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth')"
            )
        ).scalar()
        return bool(row)
    except Exception:
        return False


def _ensure_table(
    inspector: sa.Inspector,
    existing_tables: Iterable[str],
    table_name: str,
    expected_columns: Set[str],
    creator: Callable[[], None],
) -> None:
    """Verify no schema drift when present, otherwise create table cleanly."""
    if table_name in existing_tables:
        actual = {col["name"] for col in inspector.get_columns(table_name)}
        missing = expected_columns - actual
        if missing:
            raise RuntimeError(
                f"Schema drift detected in table '{table_name}': missing columns {sorted(missing)}. "
                "Migration cannot silently skip an incomplete schema."
            )
        return
    creator()


def _create_canonical_crops() -> None:
    op.create_table(
        "rashkar_canonical_crops",
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("common_name_en", sa.String(length=100), nullable=False),
        sa.Column("common_name_mr", sa.String(length=100), nullable=False),
        sa.Column("botanical_name", sa.String(length=150), nullable=False),
        sa.Column("crop_category", sa.String(length=50), nullable=False),
        sa.Column("standard_season", sa.String(length=50), nullable=False),
        sa.Column(
            "is_pioneer_pilot_crop",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "support_level",
            sa.String(length=50),
            nullable=False,
            server_default="data_limited",
        ),
        sa.Column("apy_alias_list", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("crop_code"),
    )


def _create_crop_stages() -> None:
    op.create_table(
        "rashkar_crop_stages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("stage_code", sa.String(length=50), nullable=False),
        sa.Column("stage_name_en", sa.String(length=100), nullable=False),
        sa.Column("stage_name_mr", sa.String(length=100), nullable=False),
        sa.Column("sequence_order", sa.Integer(), nullable=False),
        sa.Column("typical_das_start", sa.Integer(), nullable=False),
        sa.Column("typical_das_end", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["crop_code"],
            ["rashkar_canonical_crops.crop_code"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rashkar_crop_stages_crop_code", "rashkar_crop_stages", ["crop_code"])
    op.create_index("ix_rashkar_crop_stages_stage_code", "rashkar_crop_stages", ["stage_code"])


def _create_agronomic_thresholds() -> None:
    op.create_table(
        "rashkar_agronomic_thresholds",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("stage_code", sa.String(length=50), nullable=False),
        sa.Column("tmin_ideal_low", sa.Float(), nullable=True),
        sa.Column("tmax_ideal_high", sa.Float(), nullable=True),
        sa.Column("tmax_stress_trigger", sa.Float(), nullable=True),
        sa.Column("tmax_critical_damage", sa.Float(), nullable=True),
        sa.Column("tmin_cold_trigger", sa.Float(), nullable=True),
        sa.Column("vpd_stress_trigger_kpa", sa.Float(), nullable=True),
        sa.Column(
            "critical_heat_duration_hrs",
            sa.Integer(),
            nullable=True,
            server_default="1",
        ),
        sa.Column("evidence_tier", sa.String(length=50), nullable=False),
        sa.Column("source_citation", sa.Text(), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at_utc",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["crop_code"],
            ["rashkar_canonical_crops.crop_code"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rashkar_agronomic_thresholds_crop_code",
        "rashkar_agronomic_thresholds",
        ["crop_code"],
    )
    op.create_index(
        "ix_rashkar_agronomic_thresholds_stage_code",
        "rashkar_agronomic_thresholds",
        ["stage_code"],
    )


def _create_advisory_catalogue() -> None:
    op.create_table(
        "rashkar_advisory_catalogue",
        sa.Column("advisory_id", sa.String(length=50), nullable=False),
        sa.Column("domain", sa.String(length=50), nullable=False),
        sa.Column("target_crop_code", sa.String(length=50), nullable=False),
        sa.Column("target_stage_code", sa.String(length=50), nullable=True),
        sa.Column("trigger_severity", sa.String(length=50), nullable=False),
        sa.Column("title_en", sa.String(length=200), nullable=False),
        sa.Column("title_mr", sa.String(length=200), nullable=False),
        sa.Column("action_steps_en", sa.JSON(), nullable=False),
        sa.Column("action_steps_mr", sa.JSON(), nullable=False),
        sa.Column("do_not_do_warning", sa.Text(), nullable=True),
        sa.Column("cost_class", sa.String(length=50), nullable=True),
        sa.Column("lead_time_required_hours", sa.Integer(), nullable=True),
        sa.Column("source_attribution", sa.Text(), nullable=False),
        sa.Column(
            "is_verified_agronomist",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.PrimaryKeyConstraint("advisory_id"),
    )
    op.create_index(
        "ix_rashkar_advisory_catalogue_domain",
        "rashkar_advisory_catalogue",
        ["domain"],
    )
    op.create_index(
        "ix_rashkar_advisory_catalogue_target_crop_code",
        "rashkar_advisory_catalogue",
        ["target_crop_code"],
    )
    op.create_index(
        "ix_rashkar_advisory_catalogue_target_stage_code",
        "rashkar_advisory_catalogue",
        ["target_stage_code"],
    )


def _create_income_opportunities() -> None:
    op.create_table(
        "rashkar_income_opportunities",
        sa.Column("opportunity_id", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column(
            "is_cost_saving",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column("tagline", sa.String(length=200), nullable=True, server_default=""),
        sa.Column("target_crops", sa.JSON(), nullable=True),
        sa.Column("required_resources", sa.JSON(), nullable=True),
        sa.Column("min_investment_inr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("max_investment_inr", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column(
            "working_capital_required_inr",
            sa.Float(),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column("payback_period_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "potential_annual_profit_inr",
            sa.Float(),
            nullable=False,
            server_default="0.0",
        ),
        sa.Column(
            "potential_annual_savings_inr",
            sa.Float(),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column("risk_level", sa.String(length=20), nullable=True, server_default="moderate"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("market_commodity", sa.String(length=100), nullable=True, server_default=""),
        sa.Column(
            "market_benchmark_price",
            sa.String(length=100),
            nullable=True,
            server_default="",
        ),
        sa.Column("market_source", sa.String(length=150), nullable=True, server_default=""),
        sa.Column("key_assumptions", sa.JSON(), nullable=True),
        sa.Column("key_risks", sa.JSON(), nullable=True),
        sa.Column("source_attribution", sa.String(length=200), nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("opportunity_id"),
    )


def _create_crop_cycles() -> None:
    op.create_table(
        "rashkar_crop_cycles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("variety_name", sa.String(length=100), nullable=True),
        sa.Column("sowing_date", sa.Date(), nullable=True),
        sa.Column("season", sa.String(length=30), nullable=True),
        sa.Column("planted_area_acres", sa.Float(), nullable=True),
        sa.Column("irrigation_type", sa.String(length=50), nullable=True),
        sa.Column("current_stage_code", sa.String(length=50), nullable=True),
        sa.Column(
            "stage_source",
            sa.String(length=30),
            nullable=False,
            server_default="estimated_from_das",
        ),
        sa.Column("stage_confidence", sa.Float(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at_utc",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at_utc",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rashkar_crop_cycles_farm_id", "rashkar_crop_cycles", ["farm_id"])
    op.create_index("ix_rashkar_crop_cycles_owner_id", "rashkar_crop_cycles", ["owner_id"])
    op.create_index("ix_rashkar_crop_cycles_crop_code", "rashkar_crop_cycles", ["crop_code"])
    op.create_index("ix_rashkar_crop_cycles_is_active", "rashkar_crop_cycles", ["is_active"])


def _create_worker_hazard_audit_logs() -> None:
    op.create_table(
        "rashkar_worker_hazard_audit_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=True),
        sa.Column("owner_id", sa.String(length=36), nullable=True),
        sa.Column("request_timestamp_utc", sa.DateTime(), nullable=False),
        sa.Column("forecast_target_timestamp_utc", sa.DateTime(), nullable=False),
        sa.Column("weather_provider", sa.String(length=100), nullable=False),
        sa.Column("air_temp_c", sa.Float(), nullable=False),
        sa.Column("relative_humidity_pct", sa.Float(), nullable=False),
        sa.Column("wind_speed_kmh", sa.Float(), nullable=False),
        sa.Column("solar_radiation_wm2", sa.Float(), nullable=False),
        sa.Column("calculated_wbgt_c", sa.Float(), nullable=False),
        sa.Column("calculated_heat_index_c", sa.Float(), nullable=True),
        sa.Column("risk_tier", sa.String(length=50), nullable=False),
        sa.Column("workload_class", sa.String(length=50), nullable=False),
        sa.Column(
            "acclimatization_status",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column("applied_threshold_wbgt_c", sa.Float(), nullable=False),
        sa.Column("provenance_summary", sa.JSON(), nullable=False),
        sa.Column("advisory_issued_ids", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rashkar_worker_hazard_audit_logs_farm_id",
        "rashkar_worker_hazard_audit_logs",
        ["farm_id"],
    )
    op.create_index(
        "ix_rashkar_worker_hazard_audit_logs_owner_id",
        "rashkar_worker_hazard_audit_logs",
        ["owner_id"],
    )


def _create_crop_heat_logs() -> None:
    op.create_table(
        "rashkar_crop_heat_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("stage_code", sa.String(length=50), nullable=True),
        sa.Column("stage_source", sa.String(length=50), nullable=True),
        sa.Column("assessed_at_utc", sa.DateTime(), nullable=False),
        sa.Column("peak_tmax_c", sa.Float(), nullable=False),
        sa.Column("peak_vpd_kpa", sa.Float(), nullable=True),
        sa.Column("overall_stress_score", sa.Float(), nullable=False),
        sa.Column("stress_tier", sa.String(length=50), nullable=False),
        sa.Column("weather_source", sa.String(length=100), nullable=False),
        sa.Column("provenance_summary", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_rashkar_crop_heat_logs_farm_id", "rashkar_crop_heat_logs", ["farm_id"])
    op.create_index("ix_rashkar_crop_heat_logs_owner_id", "rashkar_crop_heat_logs", ["owner_id"])
    op.create_index("ix_rashkar_crop_heat_logs_crop_code", "rashkar_crop_heat_logs", ["crop_code"])


def _create_yield_assessment_logs() -> None:
    op.create_table(
        "rashkar_yield_assessment_logs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("crop_code", sa.String(length=50), nullable=False),
        sa.Column("district", sa.String(length=100), nullable=False),
        sa.Column("assessed_at_utc", sa.DateTime(), nullable=False),
        sa.Column("benchmark_tier", sa.String(length=50), nullable=False),
        sa.Column("apy_mean_t_ha", sa.Float(), nullable=True),
        sa.Column("apy_median_t_ha", sa.Float(), nullable=True),
        sa.Column("apy_sample_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("composite_risk_score", sa.Float(), nullable=False),
        sa.Column("composite_risk_tier", sa.String(length=50), nullable=False),
        sa.Column("prediction_lock_status", sa.String(length=50), nullable=False),
        sa.Column("provenance_summary", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_rashkar_yield_assessment_logs_farm_id",
        "rashkar_yield_assessment_logs",
        ["farm_id"],
    )
    op.create_index(
        "ix_rashkar_yield_assessment_logs_owner_id",
        "rashkar_yield_assessment_logs",
        ["owner_id"],
    )
    op.create_index(
        "ix_rashkar_yield_assessment_logs_crop_code",
        "rashkar_yield_assessment_logs",
        ["crop_code"],
    )


def _create_farmer_resource_profiles() -> None:
    op.create_table(
        "rashkar_farmer_resource_profiles",
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column(
            "available_investment_inr",
            sa.Float(),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column(
            "monthly_operating_budget_inr",
            sa.Float(),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column("max_risk_capital_inr", sa.Float(), nullable=True),
        sa.Column(
            "willing_to_borrow",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column("total_farm_acres", sa.Float(), nullable=True),
        sa.Column("cultivated_acres", sa.Float(), nullable=True),
        sa.Column("available_land_acres", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column("unused_land_acres", sa.Float(), nullable=True, server_default="0.0"),
        sa.Column(
            "field_bunds_available",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "has_animal_shed",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_storage_room",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_shaded_space",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "water_availability",
            sa.String(length=50),
            nullable=True,
            server_default="seasonal_canal",
        ),
        sa.Column("water_months_available", sa.JSON(), nullable=True),
        sa.Column(
            "family_labor_hours_day",
            sa.Float(),
            nullable=True,
            server_default="2.0",
        ),
        sa.Column(
            "hired_labor_possible",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "existing_livestock",
            sa.String(length=50),
            nullable=True,
            server_default="none",
        ),
        sa.Column("existing_assets", sa.JSON(), nullable=True),
        sa.Column("crop_byproducts", sa.JSON(), nullable=True),
        sa.Column(
            "byproduct_surplus_available",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("true"),
        ),
        sa.Column("interests", sa.JSON(), nullable=True),
        sa.Column(
            "has_transport",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "has_fpo_access",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("false"),
        ),
        sa.Column("distance_to_apmc_km", sa.Float(), nullable=True),
        sa.Column("risk_tolerance", sa.String(length=20), nullable=True, server_default="moderate"),
        sa.Column("category_preference", sa.String(length=50), nullable=True, server_default="all"),
        sa.Column("age_range", sa.String(length=30), nullable=True, server_default="36-45"),
        sa.Column(
            "work_preference",
            sa.String(length=50),
            nullable=True,
            server_default="daily_physical",
        ),
        sa.Column(
            "payback_horizon",
            sa.String(length=50),
            nullable=True,
            server_default="within_6_months",
        ),
        sa.Column(
            "family_management_role",
            sa.String(length=50),
            nullable=True,
            server_default="self",
        ),
        sa.Column("current_crop_code", sa.String(length=50), nullable=True),
        sa.Column("current_crop_stage", sa.String(length=50), nullable=True),
        sa.Column("updated_at_utc", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("farm_id"),
    )
    op.create_index(
        "ix_rashkar_farmer_resource_profiles_owner_id",
        "rashkar_farmer_resource_profiles",
        ["owner_id"],
    )


def _create_income_scenarios() -> None:
    op.create_table(
        "rashkar_income_scenarios",
        sa.Column("scenario_id", sa.String(length=50), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=50), nullable=False),
        sa.Column("custom_budget_inr", sa.Float(), nullable=False),
        sa.Column(
            "available_labour_hours_day",
            sa.Float(),
            nullable=True,
            server_default="2.0",
        ),
        sa.Column("available_land_acres", sa.Float(), nullable=True, server_default="0.5"),
        sa.Column("custom_assumptions", sa.JSON(), nullable=True),
        sa.Column("calculated_capex_inr", sa.Float(), nullable=False),
        sa.Column("calculated_opex_annual_inr", sa.Float(), nullable=False),
        sa.Column("calculated_gross_revenue_inr", sa.Float(), nullable=False),
        sa.Column("calculated_net_profit_annual_inr", sa.Float(), nullable=False),
        sa.Column("calculated_break_even_months", sa.Float(), nullable=True),
        sa.Column("sensitivity_analysis", sa.JSON(), nullable=True),
        sa.Column("monthly_cash_flows", sa.JSON(), nullable=True),
        sa.Column(
            "generated_at_utc",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["opportunity_id"],
            ["rashkar_income_opportunities.opportunity_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("scenario_id"),
    )
    op.create_index("ix_rashkar_income_scenarios_owner_id", "rashkar_income_scenarios", ["owner_id"])
    op.create_index("ix_rashkar_income_scenarios_farm_id", "rashkar_income_scenarios", ["farm_id"])


def _create_saved_income_plans() -> None:
    op.create_table(
        "rashkar_saved_income_plans",
        sa.Column("plan_id", sa.String(length=50), nullable=False),
        sa.Column("owner_id", sa.String(length=36), nullable=False),
        sa.Column("farm_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=50), nullable=False),
        sa.Column("opportunity_title", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("chosen_budget_inr", sa.Float(), nullable=False),
        sa.Column("projected_annual_profit_inr", sa.Float(), nullable=False),
        sa.Column(
            "projected_annual_savings_inr",
            sa.Float(),
            nullable=True,
            server_default="0.0",
        ),
        sa.Column("payback_months", sa.Float(), nullable=True),
        sa.Column(
            "break_even_reached",
            sa.Boolean(),
            nullable=True,
            server_default=sa.text("true"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at_utc",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("plan_id"),
    )
    op.create_index(
        "ix_rashkar_saved_income_plans_owner_id",
        "rashkar_saved_income_plans",
        ["owner_id"],
    )
    op.create_index(
        "ix_rashkar_saved_income_plans_farm_id",
        "rashkar_saved_income_plans",
        ["farm_id"],
    )


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())

    specs = [
        (
            "rashkar_canonical_crops",
            {
                "crop_code",
                "common_name_en",
                "common_name_mr",
                "botanical_name",
                "crop_category",
                "standard_season",
                "is_pioneer_pilot_crop",
                "support_level",
                "apy_alias_list",
            },
            _create_canonical_crops,
        ),
        (
            "rashkar_crop_stages",
            {
                "id",
                "crop_code",
                "stage_code",
                "stage_name_en",
                "stage_name_mr",
                "sequence_order",
                "typical_das_start",
                "typical_das_end",
                "description",
            },
            _create_crop_stages,
        ),
        (
            "rashkar_agronomic_thresholds",
            {
                "id",
                "crop_code",
                "stage_code",
                "tmin_ideal_low",
                "tmax_ideal_high",
                "tmax_stress_trigger",
                "tmax_critical_damage",
                "tmin_cold_trigger",
                "vpd_stress_trigger_kpa",
                "critical_heat_duration_hrs",
                "evidence_tier",
                "source_citation",
                "is_active",
                "created_at_utc",
            },
            _create_agronomic_thresholds,
        ),
        (
            "rashkar_advisory_catalogue",
            {
                "advisory_id",
                "domain",
                "target_crop_code",
                "target_stage_code",
                "trigger_severity",
                "title_en",
                "title_mr",
                "action_steps_en",
                "action_steps_mr",
                "do_not_do_warning",
                "cost_class",
                "lead_time_required_hours",
                "source_attribution",
                "is_verified_agronomist",
            },
            _create_advisory_catalogue,
        ),
        (
            "rashkar_income_opportunities",
            {
                "opportunity_id",
                "title",
                "category",
                "is_cost_saving",
                "tagline",
                "target_crops",
                "required_resources",
                "min_investment_inr",
                "max_investment_inr",
                "working_capital_required_inr",
                "payback_period_months",
                "potential_annual_profit_inr",
                "potential_annual_savings_inr",
                "risk_level",
                "summary",
                "market_commodity",
                "market_benchmark_price",
                "market_source",
                "key_assumptions",
                "key_risks",
                "source_attribution",
                "is_active",
                "created_at",
            },
            _create_income_opportunities,
        ),
        (
            "rashkar_crop_cycles",
            {
                "id",
                "farm_id",
                "owner_id",
                "crop_code",
                "variety_name",
                "sowing_date",
                "season",
                "planted_area_acres",
                "irrigation_type",
                "current_stage_code",
                "stage_source",
                "stage_confidence",
                "is_active",
                "created_at_utc",
                "updated_at_utc",
            },
            _create_crop_cycles,
        ),
        (
            "rashkar_worker_hazard_audit_logs",
            {
                "id",
                "farm_id",
                "owner_id",
                "request_timestamp_utc",
                "forecast_target_timestamp_utc",
                "weather_provider",
                "air_temp_c",
                "relative_humidity_pct",
                "wind_speed_kmh",
                "solar_radiation_wm2",
                "calculated_wbgt_c",
                "calculated_heat_index_c",
                "risk_tier",
                "workload_class",
                "acclimatization_status",
                "applied_threshold_wbgt_c",
                "provenance_summary",
                "advisory_issued_ids",
            },
            _create_worker_hazard_audit_logs,
        ),
        (
            "rashkar_crop_heat_logs",
            {
                "id",
                "farm_id",
                "owner_id",
                "crop_code",
                "stage_code",
                "stage_source",
                "assessed_at_utc",
                "peak_tmax_c",
                "peak_vpd_kpa",
                "overall_stress_score",
                "stress_tier",
                "weather_source",
                "provenance_summary",
            },
            _create_crop_heat_logs,
        ),
        (
            "rashkar_yield_assessment_logs",
            {
                "id",
                "farm_id",
                "owner_id",
                "crop_code",
                "district",
                "assessed_at_utc",
                "benchmark_tier",
                "apy_mean_t_ha",
                "apy_median_t_ha",
                "apy_sample_count",
                "composite_risk_score",
                "composite_risk_tier",
                "prediction_lock_status",
                "provenance_summary",
            },
            _create_yield_assessment_logs,
        ),
        (
            "rashkar_farmer_resource_profiles",
            {
                "farm_id",
                "owner_id",
                "available_investment_inr",
                "monthly_operating_budget_inr",
                "max_risk_capital_inr",
                "willing_to_borrow",
                "total_farm_acres",
                "cultivated_acres",
                "available_land_acres",
                "unused_land_acres",
                "field_bunds_available",
                "has_animal_shed",
                "has_storage_room",
                "has_shaded_space",
                "water_availability",
                "water_months_available",
                "family_labor_hours_day",
                "hired_labor_possible",
                "existing_livestock",
                "existing_assets",
                "crop_byproducts",
                "byproduct_surplus_available",
                "interests",
                "has_transport",
                "has_fpo_access",
                "distance_to_apmc_km",
                "risk_tolerance",
                "category_preference",
                "age_range",
                "work_preference",
                "payback_horizon",
                "family_management_role",
                "current_crop_code",
                "current_crop_stage",
                "updated_at_utc",
            },
            _create_farmer_resource_profiles,
        ),
        (
            "rashkar_income_scenarios",
            {
                "scenario_id",
                "owner_id",
                "farm_id",
                "opportunity_id",
                "custom_budget_inr",
                "available_labour_hours_day",
                "available_land_acres",
                "custom_assumptions",
                "calculated_capex_inr",
                "calculated_opex_annual_inr",
                "calculated_gross_revenue_inr",
                "calculated_net_profit_annual_inr",
                "calculated_break_even_months",
                "sensitivity_analysis",
                "monthly_cash_flows",
                "generated_at_utc",
            },
            _create_income_scenarios,
        ),
        (
            "rashkar_saved_income_plans",
            {
                "plan_id",
                "owner_id",
                "farm_id",
                "opportunity_id",
                "opportunity_title",
                "category",
                "chosen_budget_inr",
                "projected_annual_profit_inr",
                "projected_annual_savings_inr",
                "payback_months",
                "break_even_reached",
                "notes",
                "created_at_utc",
            },
            _create_saved_income_plans,
        ),
    ]

    for table_name, expected_cols, creator in specs:
        _ensure_table(inspector, existing_tables, table_name, expected_cols, creator)

    if _auth_schema_exists(conn):
        for ref_table in _REFERENCE_TABLES:
            op.execute(sa.text(f"ALTER TABLE public.{ref_table} ENABLE ROW LEVEL SECURITY"))
            op.execute(
                sa.text(
                    f"""
                    DROP POLICY IF EXISTS "{ref_table}_read_all" ON public.{ref_table};
                    CREATE POLICY "{ref_table}_read_all" ON public.{ref_table}
                        FOR SELECT
                        USING (true);
                    DROP POLICY IF EXISTS "{ref_table}_service_manage" ON public.{ref_table};
                    CREATE POLICY "{ref_table}_service_manage" ON public.{ref_table}
                        FOR ALL
                        USING (auth.jwt() ->> 'role' = 'service_role')
                        WITH CHECK (auth.jwt() ->> 'role' = 'service_role');
                    """
                )
            )

        for owner_table in _OWNER_SCOPED_TABLES:
            op.execute(sa.text(f"ALTER TABLE public.{owner_table} ENABLE ROW LEVEL SECURITY"))
            op.execute(
                sa.text(
                    f"""
                    DROP POLICY IF EXISTS "{owner_table}_owner_or_service" ON public.{owner_table};
                    CREATE POLICY "{owner_table}_owner_or_service" ON public.{owner_table}
                        FOR ALL
                        USING (
                            auth.uid()::text = owner_id
                            OR auth.jwt() ->> 'role' = 'service_role'
                        )
                        WITH CHECK (
                            auth.uid()::text = owner_id
                            OR auth.jwt() ->> 'role' = 'service_role'
                        );
                    """
                )
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = set(inspector.get_table_names())
    has_auth = _auth_schema_exists(conn)

    drop_order = [
        "rashkar_saved_income_plans",
        "rashkar_income_scenarios",
        "rashkar_farmer_resource_profiles",
        "rashkar_yield_assessment_logs",
        "rashkar_crop_heat_logs",
        "rashkar_worker_hazard_audit_logs",
        "rashkar_crop_cycles",
        "rashkar_income_opportunities",
        "rashkar_advisory_catalogue",
        "rashkar_agronomic_thresholds",
        "rashkar_crop_stages",
        "rashkar_canonical_crops",
    ]

    for table_name in drop_order:
        if table_name not in existing_tables:
            continue
        if has_auth:
            if table_name in _REFERENCE_TABLES:
                op.execute(
                    sa.text(
                        f"""
                        DROP POLICY IF EXISTS "{table_name}_service_manage" ON public.{table_name};
                        DROP POLICY IF EXISTS "{table_name}_read_all" ON public.{table_name};
                        ALTER TABLE public.{table_name} DISABLE ROW LEVEL SECURITY;
                        """
                    )
                )
            else:
                op.execute(
                    sa.text(
                        f"""
                        DROP POLICY IF EXISTS "{table_name}_owner_or_service" ON public.{table_name};
                        ALTER TABLE public.{table_name} DISABLE ROW LEVEL SECURITY;
                        """
                    )
                )
        op.drop_table(table_name)
