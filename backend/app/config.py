from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Support Ticketing API"
    app_version: str = "0.1.0"
    api_prefix: str = "/api/v1"
    debug: bool = False
    # Local-evaluation convenience: seed demo rows when the table is empty.
    seed_demo_data: bool = False

    database_url: str = "postgresql+psycopg2://tickets:tickets@localhost:5432/tickets"
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_recycle: int = 1800
    db_echo: bool = False

    # 127.0.0.1 is a different browser origin than localhost: without both, the
    # UI silently fails every request for anyone who opens the app by IP.
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@lru_cache
def get_settings() -> Settings:
    # Cached so the environment is parsed once per process.
    return Settings()


settings = get_settings()
