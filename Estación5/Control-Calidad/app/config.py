"""Application configuration using Pydantic BaseSettings"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class DatabaseSettings(BaseSettings):
    """PostgreSQL database configuration"""
    url: str = Field(..., alias="DATABASE_URL")
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_pre_ping: bool = True

    class Config:
        env_prefix = ""
        case_sensitive = False


class JWTSettings(BaseSettings):
    """JWT authentication configuration"""
    secret_key: str = Field(..., alias="JWT_SECRET_KEY")
    algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_hours: int = Field(default=8, alias="JWT_EXPIRATION_HOURS")
    refresh_token_expire_days: int = Field(default=30, alias="JWT_REFRESH_EXPIRATION_DAYS")

    class Config:
        env_prefix = ""
        case_sensitive = False


class PhotoStorageSettings(BaseSettings):
    """Photo storage configuration"""
    base_path: str = Field(default="/storage/photos", alias="PHOTO_STORAGE_PATH")
    max_size_kb: int = Field(default=500, alias="PHOTO_MAX_SIZE_KB")

    class Config:
        env_prefix = ""
        case_sensitive = False


class SyncSettings(BaseSettings):
    """Offline sync retry configuration"""
    initial_delay_seconds: int = Field(default=5, alias="SYNC_INITIAL_DELAY_SECONDS")
    max_retries: int = Field(default=5, alias="SYNC_MAX_RETRIES")

    @property
    def backoff_delays(self) -> list[int]:
        """Generate exponential backoff delays: [5, 10, 30, 60, 60]"""
        delays = []
        for i in range(self.max_retries):
            delay = min(self.initial_delay_seconds * (2 ** i), 60)
            delays.append(delay)
        return delays

    class Config:
        env_prefix = ""
        case_sensitive = False


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    format: str = "json"  # JSON structured logging
    output_file: str = "/var/log/fastapi/app.log"

    class Config:
        env_prefix = ""
        case_sensitive = False


class MonitoringSettings(BaseSettings):
    """Monitoring configuration"""
    grafana_password: Optional[str] = Field(default=None, alias="GRAFANA_PASSWORD")
    slack_webhook_url: Optional[str] = Field(default=None, alias="SLACK_WEBHOOK_URL")

    class Config:
        env_prefix = ""
        case_sensitive = False


class Settings(BaseSettings):
    """Main application settings combining all sub-settings"""
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = False

    database: DatabaseSettings = DatabaseSettings()
    jwt: JWTSettings = JWTSettings()
    photo_storage: PhotoStorageSettings = PhotoStorageSettings()
    sync: SyncSettings = SyncSettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()

    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"
        case_sensitive = False

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if v not in ("development", "staging", "production", "test", "testing"):
            raise ValueError("ENVIRONMENT must be 'development', 'staging', 'production', or 'test'")
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        return self.environment in ("development", "test", "testing")

    @property
    def is_test(self) -> bool:
        return self.environment in ("test", "testing")


# Global settings instance
settings = Settings()
