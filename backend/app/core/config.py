from functools import cached_property
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "JobFit Resume Agent"
    VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"
    DATABASE_URL: str = "sqlite:///./jobfit.db"
    BACKEND_CORS_ORIGINS: str = Field(
        default=(
            "http://localhost:5173,http://127.0.0.1:5173,"
            "http://localhost:5174,http://127.0.0.1:5174"
        )
    )

    LLM_MODE: Literal["mock", "real"] = "mock"
    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = "https://mx.free.codesonline.dev"
    OPENAI_MODEL: str = "gpt-5.4"
    OPENAI_REVIEW_MODEL: str = "gpt-5.4"
    OPENAI_WIRE_API: Literal["responses", "chat_completions"] = "responses"
    LLM_MAX_OUTPUT_TOKENS: int = 4096
    LLM_TEMPERATURE: float = 0
    MODEL_REASONING_EFFORT: str = "xhigh"
    JD_REASONING_EFFORT: str = "medium"
    PROFILE_REASONING_EFFORT: str = "medium"
    RESUME_REASONING_EFFORT: str = "xhigh"
    REVIEW_REASONING_EFFORT: str = "xhigh"
    JD_ANALYSIS_CHUNK_SIZE: int = 260
    DISABLE_RESPONSE_STORAGE: bool = True
    LLM_TIMEOUT_SECONDS: float = 180
    LLM_MAX_RETRIES: int = 0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @cached_property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.BACKEND_CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
