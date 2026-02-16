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


async def create_tables():
    await _configure_pgvector()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:  # type: ignore[misc]
    async with async_session() as session:
        yield session
