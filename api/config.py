"""Configuration for the LeanDeep API."""

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "LeanDeep Marker API"
    version: str = "5.1-LD5"
    debug: bool = False

    # Paths
    registry_path: str = str(
        Path(__file__).resolve().parent.parent / "build" / "markers_normalized" / "marker_registry.json"
    )
    personas_dir: str = str(Path(__file__).resolve().parent.parent / "personas")

    # Auth
    api_keys_file: str = str(Path(__file__).resolve().parent / "api_keys.json")
    require_auth: bool = False  # Disabled for dev; enable for prod

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # Engine
    default_threshold: float = 0.5
    max_text_length: int = 50_000
    max_conversation_messages: int = 200

    model_config = {"env_prefix": "LEANDEEP_"}


settings = Settings()
