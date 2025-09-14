from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List

class Settings(BaseSettings):
    POSTGRES_USER: str  = ''
    POSTGRES_PASSWORD: str = ''
    POSTGRES_PORT: str  = ''
    POSTGRES_HOST: str  = ''
    POSTGRES_DATABASE: str  = ''
    LLM_MODEL: str = ''
    LLM_PROVIDER: str = ''
    INCLUDE_TABLES: List | None = None
    TOP_K : int = 15
    DIALECT: str = ''
    MAX_DISPLAY_ROWS: int = 100   # Maximum rows to display in UI response
    SAMPLE_SIZE_FOR_GRAPH: int = 15

    # Optional Bedrock fields (conditionally required)
    BEDROCK_ACCESS_KEY_ID: str | None = None
    BEDROCK_SECRET_ACCESS_KEY: str | None = None
    BEDROCK_REGION: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

    @field_validator('BEDROCK_ACCESS_KEY_ID', 'BEDROCK_SECRET_ACCESS_KEY', 'BEDROCK_REGION', mode="before")
    @classmethod
    def require_bedrock_fields_if_nova(cls, v, info):
        provider = info.data.get("LLM_PROVIDER", "").lower()
        model = info.data.get("LLM_MODEL", "").lower()

        if provider == "bedrock" and "nova" in model:
            if not v:
                raise ValueError(f"{info.field_name} is required when using Bedrock with a Nova model")
        return v


settings = Settings()
# print(settings)