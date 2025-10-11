from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    project_url: str = Field(alias="SUPABASE_URL", default="")
    publishable_key: str = Field(alias="SUPABASE_PUBLISHABLE_KEY", default="")
    secret_key: str = Field(alias="SUPABASE_SECRET_KEY", default="")
