import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Charm API"
    debug: bool = False

    database_url: str

    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_ttl_minutes: int = 60

    backend_cors_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        if not self.backend_cors_origins:
            return []

        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


settings = Settings()  # type: ignore[call-arg]
