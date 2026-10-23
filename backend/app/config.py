from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pydantic import Field

load_dotenv()   # also puts .env values into the environment, where Langfuse looks for its keys

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "HR Triage"
    llm_api_key: str
    extraction_model: str = "gpt-5.4-nano"   # chosen by the eval: same accuracy, ~4x cheaper
    draft_model: str = "gpt-5.4-mini"   # blind A/B on 23 drafts: nano 14/23 sendable vs mini 19/23
    llm_base_url: str | None = None          # None = OpenAI; set it to use another provider
    database_url: str
    hr_username: str = "hr"
    hr_password: str = Field(min_length=12)  # required: no password, no start
    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_base_url: str | None = None
    
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]



settings = Settings()