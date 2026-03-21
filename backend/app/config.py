from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    SECRET_KEY: str = ""
    ENVIRONMENT: str = "development"
    FRONTEND_URL: str = "http://localhost:3001"

    @property
    def frontend_origins(self) -> list[str]:
        origins = [origin.strip() for origin in self.FRONTEND_URL.split(",")]
        return [origin for origin in origins if origin]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
