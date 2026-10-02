from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
TEMPLATES_DIR = ROOT_DIR / "templates"
STATIC_DIR = ROOT_DIR / "static"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QSHIELD_", env_file=".env", extra="ignore")

    identity_salt: str = "Q-SHIELD-SECRET-SALT"
    encryption_key: str = ""
    similarity_threshold: float = 0.85
    review_threshold: float = 0.60
    host: str = "127.0.0.1"
    port: int = 8080
    database_path: Path = DATA_DIR / "qshield.db"
    key_file: Path = DATA_DIR / ".encryption_key"


settings = Settings()
DATA_DIR.mkdir(parents=True, exist_ok=True)
