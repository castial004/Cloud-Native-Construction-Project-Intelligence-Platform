"""Central configuration for the CCPIP platform."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Prefix avoids collisions with Kubernetes auto-injected Service env vars
    # (e.g. an 'ingestion' Service injects INGESTION_PORT/INGESTION_HOST).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", env_prefix="CCPIP_")

    # Database
    database_url: str = "postgresql+psycopg2://ccpip:ccpip@localhost:5432/ccpip"

    # Ingestion service
    ingestion_host: str = "0.0.0.0"
    ingestion_port: int = 8000

    # Analytics service
    analytics_batch_size: int = 5000

    # Risk model
    risk_model_path: str = "eval/artifacts/risk_model.joblib"
    risk_model_version: str = "v1"
    delay_threshold_days: float = 5.0

    # Random seed for reproducibility
    random_seed: int = 42


settings = Settings()
