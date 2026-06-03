"""Async PostgreSQL database connection and session management"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
from loguru import logger
from typing import AsyncGenerator

from app.config import settings


# Global engine and session factory
engine = None
async_session_factory = None


async def init_db():
    """Initialize database engine and session factory"""
    global engine, async_session_factory

    db_url = settings.database.url

    engine = create_async_engine(
        db_url,
        echo=settings.database.echo,
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_pre_ping=settings.database.pool_pre_ping,
        pool_recycle=3600,  # Recycle connections after 1 hour
        connect_args={"server_settings": {"application_name": "fastapi_qc"}}
    )

    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False
    )

    logger.info("Database engine initialized", url=db_url)


async def close_db():
    """Close database engine"""
    global engine
    if engine:
        await engine.dispose()
        logger.info("Database engine closed")


def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database session"""
    @asynccontextmanager
    async def _get_session() -> AsyncGenerator[AsyncSession, None]:
        if async_session_factory is None:
            raise RuntimeError("Database not initialized. Call init_db() first.")

        async with async_session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    return _get_session()


async def get_db_connection():
    """Get a database connection for raw SQL queries"""
    if engine is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with engine.begin() as conn:
        yield conn
