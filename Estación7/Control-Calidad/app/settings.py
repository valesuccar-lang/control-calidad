"""Detailed application settings with validation and helpers"""
import os
import logging
from pathlib import Path
from loguru import logger
from app.config import settings, DatabaseSettings, JWTSettings, PhotoStorageSettings, SyncSettings, LoggingSettings


class ApplicationSettings:
    """Singleton for application-wide settings with initialization hooks"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.config = settings
        self._setup_logging()
        self._validate_database_config()
        self._validate_jwt_config()
        self._validate_photo_storage_config()
        self._initialized = True

    def _setup_logging(self) -> None:
        """Configure loguru for JSON structured logging"""
        log_level = self.config.logging.level
        log_file = self.config.logging.output_file

        # Remove default handler
        logger.remove()

        # Add console handler with format based on environment
        if self.config.is_production:
            logger.add(
                lambda msg: print(msg, end=""),
                format="{message}",
                level=log_level,
                serialize=True  # JSON output
            )
        else:
            logger.add(
                lambda msg: print(msg, end=""),
                format="<level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
                level=log_level,
                colorize=True
            )

        # Add file handler (JSON)
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            format="{message}",
            level=log_level,
            serialize=True,  # JSON format
            rotation="500 MB",  # Rotate every 500MB
            retention="30 days"  # Keep 30 days
        )

        logger.info(
            "Logging initialized",
            environment=self.config.environment,
            level=log_level,
            file=log_file
        )

    def _validate_database_config(self) -> None:
        """Validate PostgreSQL connection configuration"""
        db_url = self.config.database.url

        if not db_url.startswith("postgresql+asyncpg://"):
            raise ValueError(
                f"DATABASE_URL must use postgresql+asyncpg:// scheme, got: {db_url[:30]}..."
            )

        logger.info(
            "Database config validated",
            pool_size=self.config.database.pool_size,
            max_overflow=self.config.database.max_overflow,
            echo=self.config.database.echo
        )

    def _validate_jwt_config(self) -> None:
        """Validate JWT configuration"""
        secret_key = self.config.jwt.secret_key

        if self.config.is_production and len(secret_key) < 32:
            raise ValueError(
                "JWT_SECRET_KEY must be at least 32 characters in production"
            )

        if self.config.jwt.algorithm not in ("HS256", "HS512", "RS256"):
            raise ValueError(
                f"JWT_ALGORITHM must be HS256, HS512, or RS256, got: {self.config.jwt.algorithm}"
            )

        logger.info(
            "JWT config validated",
            algorithm=self.config.jwt.algorithm,
            access_token_expire_hours=self.config.jwt.access_token_expire_hours,
            refresh_token_expire_days=self.config.jwt.refresh_token_expire_days
        )

    def _validate_photo_storage_config(self) -> None:
        """Validate photo storage configuration"""
        base_path = self.config.photo_storage.base_path
        max_size = self.config.photo_storage.max_size_kb

        # Create storage directory if not exists
        Path(base_path).mkdir(parents=True, exist_ok=True)

        if max_size < 100 or max_size > 1000:
            raise ValueError(
                f"PHOTO_MAX_SIZE_KB must be between 100 and 1000, got: {max_size}"
            )

        logger.info(
            "Photo storage config validated",
            base_path=base_path,
            max_size_kb=max_size
        )

    def get_database_settings(self) -> DatabaseSettings:
        """Get database configuration"""
        return self.config.database

    def get_jwt_settings(self) -> JWTSettings:
        """Get JWT configuration"""
        return self.config.jwt

    def get_photo_storage_settings(self) -> PhotoStorageSettings:
        """Get photo storage configuration"""
        return self.config.photo_storage

    def get_sync_settings(self) -> SyncSettings:
        """Get sync retry configuration with backoff delays"""
        return self.config.sync

    def get_logging_settings(self) -> LoggingSettings:
        """Get logging configuration"""
        return self.config.logging

    def get_backoff_delays(self) -> list[int]:
        """Get exponential backoff delays for sync retries"""
        return self.config.sync.backoff_delays

    def is_production(self) -> bool:
        """Check if running in production"""
        return self.config.is_production

    def is_development(self) -> bool:
        """Check if running in development"""
        return self.config.is_development


# Singleton instance
app_settings = ApplicationSettings()
