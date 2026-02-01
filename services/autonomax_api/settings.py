from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=None, extra="ignore")

    # Prefer SECURITY_SECRET_KEY but accept SECRET_KEY for compatibility
    security_secret_key: str | None = Field(default=None, alias="SECURITY_SECRET_KEY")
    secret_key: str | None = Field(default=None, alias="SECRET_KEY")

    admin_secret_key: str | None = Field(default=None, alias="ADMIN_SECRET_KEY")

    database_url: str | None = Field(default=None, alias="DATABASE_URL")

    # Runtime
    environment: str = Field(default="production", alias="ENVIRONMENT")
    debug: bool = Field(default=False, alias="DEBUG")
    cors_origins: str = Field(default="*", alias="SECURITY_CORS_ORIGINS")

    # Rate-limit seconds for ops tasks
    ops_lock_ttl_seconds: int = Field(default=120, alias="OPS_LOCK_TTL_SECONDS")

    def effective_secret(self) -> str:
        return self.security_secret_key or self.secret_key or "dev-insecure-secret"

settings = Settings()
