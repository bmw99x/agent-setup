#!/bin/bash
cat > /app/app/config/settings.py <<'PY'
from dotenv import find_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=find_dotenv(".env"), extra="ignore")

    database_url: str
    sentry_dsn: str | None = None
    log_level: str = "INFO"


settings = Settings()
PY
