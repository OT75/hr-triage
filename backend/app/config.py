from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    app_name: str = "HR Triage"
    llm_api_key: str
    extraction_model: str = "gpt-5.4-nano"   # chosen by the eval: same accuracy, ~4x cheaper
    draft_model: str = "gpt-5.4-mini"        # drafting not evaluated yet, so keep the stronger model
    llm_base_url: str | None = None       # None = OpenAI; set it to use another provider
    database_url: str
    hr_username: str = "hr"
    hr_password: str                      # required: no password, no start



settings = Settings()