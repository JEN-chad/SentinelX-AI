"""SentinelX AI Application Configuration

Enforces global safety constraints including mandatory simulation-only execution.
"""

from enum import Enum
from typing import Literal, Optional
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ExecutionMode(str, Enum):
    SIMULATION = "simulation"


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Core App
    app_name: str = Field(default="SentinelX AI", alias="APP_NAME")
    environment: str = Field(default="development", alias="ENVIRONMENT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    timezone: str = "UTC"

    # CRITICAL SAFETY BOUNDARY:
    # Must strictly be 'simulation'. Production or uncontrolled autonomous execution is prohibited.
    execution_mode: str = Field(default="simulation", alias="EXECUTION_MODE")

    # Safety Guardrails
    simulation_only: bool = True
    reject_unknown_actions: bool = True
    require_approval_for_simulated_block: bool = True
    allow_production_actions: bool = False

    # Database
    database_url: str = Field(
        default="postgresql://sentinelx:sentinelx@localhost:5432/sentinelx_db",
        alias="DATABASE_URL"
    )
    neon_db_url: Optional[str] = Field(default=None, alias="NEON_DB_URL")
    secret_key: str = Field(
        default="sentinelx-dev-secret-key-replace-in-production",
        alias="SECRET_KEY"
    )

    @model_validator(mode="after")
    def resolve_neon_database_url(self) -> "Settings":
        """Prioritize cloud Neon PostgreSQL URL if present."""
        if self.neon_db_url:
            # If database_url is the local default or not set, use Neon
            if not self.database_url or "localhost:5432" in self.database_url:
                self.database_url = self.neon_db_url
        return self

    @field_validator("execution_mode")
    @classmethod
    def validate_simulation_only(cls, value: str) -> str:
        clean_val = value.strip().lower()
        if clean_val != ExecutionMode.SIMULATION.value:
            raise ValueError(
                f"SAFETY VIOLATION: SentinelX AI only permits execution_mode='simulation'. "
                f"Received '{value}'. Real network or production execution is strictly blocked."
            )
        return clean_val

    @field_validator("allow_production_actions")
    @classmethod
    def validate_no_production_actions(cls, value: bool) -> bool:
        if value is True:
            raise ValueError(
                "SAFETY VIOLATION: allow_production_actions must be False. "
                "SentinelX AI operates exclusively in offline simulation/replay mode."
            )
        return False


settings = Settings()
