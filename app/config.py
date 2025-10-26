from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    project_url: str = Field(alias="SUPABASE_URL", default="")
    supabase_service_key: str = Field(alias="SUPABASE_SECRET_KEY", default="")
    db_user: str = Field(alias="DB_USER", default="")
    db_pass: str = Field(alias="DB_PASS", default="")
    db_name: str = Field(alias="DB_NAME", default="")
    db_host: str = Field(alias="DB_HOST", default="")
    db_port: int = Field(alias="DB_PORT", default=5432)

    # HelloSign (Dropbox Sign) configuration
    hellosign_api_key: str = Field(alias="HELLOSIGN_API_KEY", default="")
    hellosign_client_id: str = Field(alias="HELLOSIGN_CLIENT_ID", default="")


def get_settings() -> Settings:
    """Obtiene la configuración de la app."""
    return Settings()
