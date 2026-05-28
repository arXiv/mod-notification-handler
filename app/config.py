from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CLASSIC_DB_URI: str = "sqlite:///:memory:"
    ENV: str = 'LOCAL'

    LOG_LEVEL: str = "INFO"

    #email related
    SEND_EMAILS: bool = False
    MAIL_FROM: str = "e-prints@arxiv.org"
    HALON_CREDS: str = "smtps://user:pass@host:port"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()