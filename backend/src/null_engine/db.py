import structlog
from sqlalchemy import JSON, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from null_engine.config import settings
from null_engine.models.base import Base

engine = create_async_engine(settings.database_url, echo=False, pool_size=20, max_overflow=10)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
logger = structlog.get_logger()
_pgvector_enabled = True


def pgvector_enabled() -> bool:
    return _pgvector_enabled


def _is_vector_column(column_type: object) -> bool:
    return column_type.__class__.__name__.lower() == "vector"


def _apply_vector_json_fallback() -> int:
    """Replace pgvector columns with JSON columns so startup can proceed without extension."""
    replaced = 0
    for table in Base.metadata.tables.values():
        for column in table.columns:
            if _is_vector_column(column.type):
                column.type = JSON()
                replaced += 1
    return replaced


async def _configure_pgvector() -> None:
    global _pgvector_enabled

    async with engine.connect() as conn:
        if conn.dialect.name != "postgresql":
            replaced = _apply_vector_json_fallback()
            _pgvector_enabled = False
            logger.info(
                "db.non_postgres_using_json_fallback",
                dialect=conn.dialect.name,
                replaced_columns=replaced,
            )
            return

        try:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.commit()
            _pgvector_enabled = True
        except Exception as exc:
            await conn.rollback()
            if settings.pgvector_required:
                raise RuntimeError(
                    "pgvector extension is required but unavailable. "
                    "Install pgvector on PostgreSQL or set PGVECTOR_REQUIRED=false."
                ) from exc
            replaced = _apply_vector_json_fallback()
            _pgvector_enabled = False
            logger.warning(
                "db.pgvector_unavailable_using_json_fallback",
                replaced_columns=replaced,
                error=str(exc),
            )


def _alembic_config():
    from pathlib import Path

    from alembic.config import Config

    backend_dir = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_dir / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    return cfg


async def _table_exists(name: str) -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT to_regclass(:name)"), {"name": name})
        return result.scalar() is not None


BASELINE_REVISION = "0001_baseline"
# Serializes schema setup across workers (pg_advisory_lock key).
_MIGRATION_LOCK_KEY = 0x6E756C6C  # "null"


async def _stamped_revisions() -> set[str]:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version_num FROM alembic_version"))
        return {row[0] for row in result.all()}


async def _embedding_column_is_vector() -> bool:
    """Detect whether the legacy schema really has pgvector columns.

    A schema built by the JSON fallback has jsonb embedding columns; it
    must not be stamped as the vector baseline.
    """
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "SELECT format_type(atttypid, atttypmod) FROM pg_attribute "
                "WHERE attrelid = 'agents'::regclass AND attname = 'embedding' "
                "AND NOT attisdropped"
            )
        )
        column_type = result.scalar() or ""
        return column_type.startswith("vector")


async def run_migrations() -> None:
    """Bring the schema to head via Alembic.

    Legacy databases were created by metadata.create_all() and never
    stamped; those are stamped at the *baseline* and then upgraded, so
    post-baseline migrations still run. (Embedding-dim reconcile for them
    is a documented one-off: migrations/reconcile_embedding_dim_1024.sql.)
    """
    import asyncio

    from alembic import command
    from alembic.script import ScriptDirectory

    cfg = _alembic_config()
    has_version = await _table_exists("alembic_version")
    has_schema = await _table_exists("worlds")

    known_revisions = {
        rev.revision for rev in ScriptDirectory.from_config(cfg).walk_revisions()
    }
    stale_version = False
    if has_version:
        stamped = await _stamped_revisions()
        stale_version = bool(stamped - known_revisions)
        if stale_version:
            logger.warning(
                "db.stale_alembic_version",
                stamped=sorted(stamped),
                hint="rows point at revisions from the removed pre-baseline chain",
            )

    if has_version and not stale_version:
        # Normal path — command.* is sync and env.py calls asyncio.run();
        # run in a thread so it gets its own event loop.
        await asyncio.to_thread(command.upgrade, cfg, "head")
        action = "upgrade"
    elif not has_schema:
        # Fresh database (purge any stale version rows first so upgrade
        # doesn't trip over revisions from the removed chain).
        if stale_version:
            await asyncio.to_thread(command.stamp, cfg, "base", purge=True)
        await asyncio.to_thread(command.upgrade, cfg, "head")
        action = "upgrade"
    else:
        # Legacy create_all() schema (or one stamped by the deleted chain).
        if not await _embedding_column_is_vector():
            raise RuntimeError(
                "Existing schema uses the JSON embedding fallback and cannot be "
                "stamped as the pgvector baseline. Convert the embedding/centroid "
                "columns to vector(1024) first (see "
                "migrations/reconcile_embedding_dim_1024.sql) or rebuild the database."
            )
        await asyncio.to_thread(command.stamp, cfg, BASELINE_REVISION, purge=True)
        await asyncio.to_thread(command.upgrade, cfg, "head")
        action = "stamp_baseline_then_upgrade"
        logger.warning(
            "db.legacy_schema_stamped",
            hint="pre-alembic database detected; if vector columns are still "
            "1536-dim run migrations/reconcile_embedding_dim_1024.sql",
        )
    logger.info("db.migrations_applied", action=action)


async def create_tables():
    # Serialize schema setup across workers: concurrent CREATE EXTENSION /
    # CREATE TABLE / alembic stamp+upgrade would race on a fresh database.
    async with engine.connect() as lock_conn:
        is_postgres = lock_conn.dialect.name == "postgresql"
        if is_postgres:
            await lock_conn.execute(
                text("SELECT pg_advisory_lock(:key)"), {"key": _MIGRATION_LOCK_KEY}
            )
        try:
            await _configure_pgvector()
            if _pgvector_enabled:
                await run_migrations()
            else:
                # Dev/CI fallback (non-postgres or missing pgvector): the
                # migration chain requires the vector type, so build the
                # JSON-column variant directly from the patched metadata.
                async with engine.begin() as conn:
                    await conn.run_sync(Base.metadata.create_all)
        finally:
            if is_postgres:
                await lock_conn.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": _MIGRATION_LOCK_KEY}
                )


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session() as session:
        yield session
