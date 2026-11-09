"""Government Schemes reference table

Revision ID: 009_government_schemes
Revises: 008_isolate_synthetic_satellite_qa
Create Date: 2026-11-09 21:45:00.000000

Adds the `government_schemes` table for verified Central and State Government
agricultural schemes. Read access is public; write access is admin-only at the
API layer. On Supabase, Row Level Security is enabled (see infra/db/schemes_rls.sql
for the canonical policy statements) — the guarded inline application below only
runs when the `auth` schema exists.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "009_government_schemes"
down_revision: Union[str, None] = "008_isolate_synthetic_satellite_qa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _auth_schema_exists(conn) -> bool:
    """True when running against a Supabase database (auth schema present)."""
    try:
        row = conn.execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'auth')"
            )
        ).scalar()
        return bool(row)
    except Exception:
        return False


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    expected_cols = {
        "id", "scheme_name", "category", "government_level", "state",
        "description", "benefits", "eligibility", "required_documents",
        "application_steps", "department", "application_url", "source_url",
        "status", "verification_status", "last_verified_date",
        "created_at", "updated_at",
    }

    if "government_schemes" in existing_tables:
        existing = {c["name"] for c in inspector.get_columns("government_schemes")}
        missing = expected_cols - existing
        if missing:
            raise RuntimeError(
                f"Schema drift detected in table 'government_schemes': missing columns {sorted(missing)}. "
                "Migration cannot silently skip an incomplete schema."
            )
    else:
        op.create_table(
            "government_schemes",
            sa.Column("id", sa.String(36), primary_key=True),
            sa.Column("scheme_name", sa.String(200), nullable=False, index=True),
            sa.Column("category", sa.String(50), nullable=False, index=True),
            sa.Column("government_level", sa.String(20), nullable=False, index=True),
            sa.Column("state", sa.String(60), nullable=True, index=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("benefits", sa.JSON(), nullable=True),
            sa.Column("eligibility", sa.JSON(), nullable=True),
            sa.Column("required_documents", sa.JSON(), nullable=True),
            sa.Column("application_steps", sa.JSON(), nullable=True),
            sa.Column("department", sa.String(200), nullable=True),
            sa.Column("application_url", sa.Text(), nullable=True),
            sa.Column("source_url", sa.Text(), nullable=True),
            sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE", index=True),
            sa.Column("verification_status", sa.String(30), nullable=False, server_default="VERIFIED", index=True),
            sa.Column("last_verified_date", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index(
            "ix_government_schemes_category_status",
            "government_schemes",
            ["category", "status"],
        )
        op.create_index(
            "ix_government_schemes_level_state_status",
            "government_schemes",
            ["government_level", "state", "status"],
        )

    # Enable Supabase Row Level Security (only when the auth schema is present).
    if _auth_schema_exists(conn):
        op.execute(sa.text("ALTER TABLE public.government_schemes ENABLE ROW LEVEL SECURITY"))

        # Public read: only active + verified schemes are visible to anon/authenticated roles.
        op.execute(
            sa.text(
                """
                DROP POLICY IF EXISTS "schemes_public_read" ON public.government_schemes;
                CREATE POLICY "schemes_public_read" ON public.government_schemes
                    FOR SELECT
                    USING (status = 'ACTIVE' AND verification_status = 'VERIFIED');
                """
            )
        )

        # Admin write: restricted to the service_role (used by the backend / migrations).
        op.execute(
            sa.text(
                """
                DROP POLICY IF EXISTS "schemes_admin_manage" ON public.government_schemes;
                CREATE POLICY "schemes_admin_manage" ON public.government_schemes
                    FOR ALL
                    USING (auth.jwt() ->> 'role' = 'service_role')
                    WITH CHECK (auth.jwt() ->> 'role' = 'service_role');
                """
            )
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    if "government_schemes" in existing_tables:
        if _auth_schema_exists(conn):
            op.execute(
                sa.text(
                    """
                    DROP POLICY IF EXISTS "schemes_admin_manage" ON public.government_schemes;
                    DROP POLICY IF EXISTS "schemes_public_read" ON public.government_schemes;
                    ALTER TABLE public.government_schemes DISABLE ROW LEVEL SECURITY;
                    """
                )
            )
        op.drop_index("ix_government_schemes_level_state_status", table_name="government_schemes")
        op.drop_index("ix_government_schemes_category_status", table_name="government_schemes")
        op.drop_table("government_schemes")
