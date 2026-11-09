import sys
import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Add repository root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))

from cropnet.services.api.app.models.soil_and_farm import Base
from cropnet.services.api.app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _get_target_url() -> str:
    if os.environ.get("DATABASE_URL"):
        url = os.environ["DATABASE_URL"]
    elif config.get_main_option("sqlalchemy.url") and config.get_main_option("sqlalchemy.url") != "sqlite:///./cropnet_dev.db":
        url = config.get_main_option("sqlalchemy.url")
    elif getattr(settings, "SYNC_DATABASE_URL", None):
        url = settings.SYNC_DATABASE_URL
    else:
        url = config.get_main_option("sqlalchemy.url")

    if url and url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if url and "@localhost:" in url:
        url = url.replace("@localhost:", "@127.0.0.1:")
    return url


def run_migrations_offline() -> None:
    url = _get_target_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _get_target_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
