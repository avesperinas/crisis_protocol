from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from src.config import settings


class Base(DeclarativeBase):
    pass


engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db() -> None:
    # Import all models so they're registered on Base.metadata before create_all.
    from src import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await _apply_migrations(conn)


async def _apply_migrations(conn) -> None:
    """Add columns introduced after initial schema (SQLite ALTER TABLE migration)."""
    result = await conn.execute(text("PRAGMA table_info(games)"))
    existing = {row[1] for row in result.fetchall()}
    pending = [
        ("mode",         "ALTER TABLE games ADD COLUMN mode TEXT NOT NULL DEFAULT 'solo'"),
        ("join_code",    "ALTER TABLE games ADD COLUMN join_code TEXT"),
        ("host_role_id", "ALTER TABLE games ADD COLUMN host_role_id TEXT"),
        ("room_name",    "ALTER TABLE games ADD COLUMN room_name TEXT"),
        ("turn_timeout_seconds", "ALTER TABLE games ADD COLUMN turn_timeout_seconds INTEGER"),
    ]
    for col, sql in pending:
        if col not in existing:
            await conn.execute(text(sql))
