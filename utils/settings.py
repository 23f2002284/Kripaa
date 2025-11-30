from pydantic_settings import BaseSettings
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

class Settings(BaseSettings):
    """Manages application settings and environment variables."""

    google_api_key: Optional[SecretStr] = Field(default=None, alias="GOOGLE_API_KEY")
    ocr_fallback_threshold: int = Field(default=26, alias="OCR_FALLBACK_THRESHOLD")
    variant_grouping_threshold: float = Field(default=0.85, alias="VARIANT_GROUPING_THRESHOLD")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

settings = Settings()