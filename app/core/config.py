from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import os


class Settings(BaseSettings):
    app_name: str = "AgentShelf"
    app_version: str = "0.6.1"
    debug: bool = True

    # Claude API (used ONLY for visibility testing on Claude platform)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"

    # DeepSeek API (used for diagnostics, optimization, query gen, extraction)
    deepseek_api_key: str = ""
    deepseek_model: str = "deepseek-chat"

    # Gemini API (used for visibility testing on Gemini platform)
    gemini_api_key: str = ""
    serpapi_key: str = ""

    # Firecrawl API (for JS-rendered page extraction)
    firecrawl_api_key: str = ""

    # OpenAI API (for multi-LLM visibility testing)
    openai_api_key: str = ""

    # Perplexity Sonar API (for multi-LLM visibility testing)
    perplexity_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./agentshelf.db"
    sqlite_path: str = "./agentshelf.db"

    # Auth / JWT
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080  # 7 days

    # Email (Resend)
    resend_api_key: str = ""
    email_from: str = "AgentShelf <noreply@agentshelf.co>"
    frontend_url: str = "https://agentshelf.co"

    # Polar (payments)
    polar_access_token: str = ""
    polar_webhook_secret: str = ""
    polar_product_pro: str = "582a3ec5-800c-4780-9368-c22980ff2690"
    polar_product_growth: str = "84f9fad2-4afd-438f-8abb-5b7d16c458e1"

    # CORS
    allowed_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://agentshelf.co",
        "https://www.agentshelf.co",
    ]

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v):
        if isinstance(v, str):
            # Support comma-separated or JSON array from env var
            v = v.strip()
            if v.startswith("["):
                import json
                return json.loads(v)
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
