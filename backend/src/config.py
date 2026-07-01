from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    database_url: str = "sqlite+aiosqlite:///./crisis_protocol.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    # Set HAIKU_ONLY=true to force all Claude calls to use Haiku (cheaper for testing).
    haiku_only: bool = False
    # Seconds before an idle human player gets an auto-submitted action. 0 = disabled.
    turn_timeout_seconds: int = 300
    # JWT auth. Override JWT_SECRET_KEY via env in any non-local deployment.
    jwt_secret_key: str = "dev-insecure-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_minutes: int = 15
    jwt_refresh_token_days: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
