"""
Hermes REST API — Configuration.

All tunable settings in one place.
"""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings from environment variables."""

    # Identity
    app_name: str = "Hermes REST API"
    version: str = "0.1.0"

    # Server — MUST NOT conflict with Governor (8003) or vLLM (8001)
    host: str = "0.0.0.0"
    port: int = 8010

    # Governor (request budget/rate-limit layer)
    governor_base_url: str = "http://127.0.0.1:8003/v1"
    governor_timeout: float = 300.0  # seconds — inference can take time
    governor_max_retries: int = 2

    # vLLM (direct fallback, bypasses Governor)
    vllm_base_url: str = "http://127.0.0.1:8001/v1"

    # SQLite session database
    db_path: str = "./data/sessions.db"

    # Continuity engine
    continuity_confidence_threshold: float = 0.7
    continuity_entity_threshold: float = 0.4

    # Logging
    log_level: str = "INFO"

    model_config = {"env_prefix": "HERMES_API_", "env_file": ".env"}


# Singleton — imported everywhere
settings = Settings()
