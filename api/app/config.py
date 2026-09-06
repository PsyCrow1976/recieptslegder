from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://receiptslegder:receiptslegder@db:5432/receiptslegder"
    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    admin_username: str = "admin"
    admin_password: str = "admin"
    document_storage_path: str = "/app/data/documents"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
