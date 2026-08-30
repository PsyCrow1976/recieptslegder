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
    cors_origins: str = "http://localhost:8090,http://192.168.1.130:8090"
    receipt_storage_path: str = "/app/data/receipts"
    xai_api_key: str = ""
    xai_model: str = "grok-4.6"
    xai_base_url: str = "https://api.x.ai/v1"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
