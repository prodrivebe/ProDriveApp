"""Environment-driven application settings."""

from functools import lru_cache

from pydantic import Field, RedisDsn, computed_field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_CORS_ALLOWED_ORIGINS: list[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://prodriveservice.eu",
    "https://www.prodriveservice.eu",
]


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="ProDrive API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    environment: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    postgres_user: str = Field(default="prodrive", alias="POSTGRES_USER")
    postgres_password: str = Field(default="prodrive", alias="POSTGRES_PASSWORD")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="prodrive", alias="POSTGRES_DB")

    database_url_override: str | None = Field(
        default=None,
        alias="DATABASE_URL",
    )

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")

    redis_url_override: RedisDsn | None = Field(default=None, alias="REDIS_URL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    jwt_secret_key: str = Field(
        default="change-me-in-production",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=15,
        alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    jwt_refresh_token_expire_days: int = Field(
        default=7,
        alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS",
    )
    password_reset_token_expire_hours: int = Field(
        default=1,
        alias="PASSWORD_RESET_TOKEN_EXPIRE_HOURS",
    )

    seed_admin_email: str = Field(
        default="admin@example.com",
        alias="SEED_ADMIN_EMAIL",
    )
    seed_admin_password: str = Field(
        default="Admin123!",
        alias="SEED_ADMIN_PASSWORD",
    )
    seed_company_name: str = Field(
        default="ProDrive Demo Transport",
        alias="SEED_COMPANY_NAME",
    )
    upload_root_dir: str = Field(default="uploads", alias="UPLOAD_ROOT_DIR")
    max_logo_size_mb: int = Field(default=5, alias="MAX_LOGO_SIZE_MB")
    max_photo_size_mb: int = Field(default=10, alias="MAX_PHOTO_SIZE_MB")
    max_document_size_mb: int = Field(default=15, alias="MAX_DOCUMENT_SIZE_MB")
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: list(DEFAULT_CORS_ALLOWED_ORIGINS),
        alias="CORS_ALLOWED_ORIGINS",
    )

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> list[str]:
        """Allow comma-separated CORS origins from environment variables."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if value is None:
            return list(DEFAULT_CORS_ALLOWED_ORIGINS)
        return value  # type: ignore[return-value]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def database_url(self) -> str:
        """Return the SQLAlchemy database URL."""
        if self.database_url_override is not None:
            return str(self.database_url_override)
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def redis_url(self) -> str:
        """Return the Redis connection URL."""
        if self.redis_url_override is not None:
            return str(self.redis_url_override)
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
