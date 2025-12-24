"""Alembic environment configuration."""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add the app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import database models
from database.database import Base

# Get DATABASE_URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Try to derive from SUPABASE_URL
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    if SUPABASE_URL:
        try:
            project_ref = SUPABASE_URL.split("://")[1].split(".")[0]
            DATABASE_URL = f"postgresql://postgres:{DB_PASSWORD}@db.{project_ref}.supabase.co:5432/postgres"
        except:
            pass

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in environment")

# this is the Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model's MetaData object for 'autogenerate' support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        {"sqlalchemy.url": DATABASE_URL},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
