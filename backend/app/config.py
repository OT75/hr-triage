from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "HR Triage"
    llm_api_key: str = ""
    llm_model: str = "gpt-5.4-mini"
    llm_base_url: str | None = None       # None = OpenAI; set it to use another provider



settings = Settings()