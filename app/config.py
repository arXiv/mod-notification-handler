from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CLASSIC_DB_URL: str
    ENV: str = 'LOCAL'

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()