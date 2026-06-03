"""Application lifespan events (startup/shutdown)"""
from contextlib import asynccontextmanager
from loguru import logger
from app.database import init_db, close_db


@asynccontextmanager
async def lifespan(app):
    """FastAPI lifespan context manager for startup/shutdown"""
    # Startup
    logger.info("Starting FastAPI application")
    await init_db()
    logger.info("Database connection pool initialized")
    yield
    # Shutdown
    logger.info("Shutting down FastAPI application")
    await close_db()
    logger.info("Database connection pool closed")
