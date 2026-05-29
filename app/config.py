from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CLASSIC_DB_URI: str = "sqlite:///:memory:"
    ENV: str = 'LOCAL'

    LOG_LEVEL: str = "INFO"

    #email related
    SEND_EMAILS: bool = False
    SMTP_PASSWORD: str = "not-configured"
    SMTP_HOST: str = "mailh.arxiv.org"
    SMTP_USER: str = "arxiv"
    MAIL_FROM: str = "e-prints@arxiv.org"
    REDIRECT_RECIPIENT: Optional[str] = None
    ARCHIVAL_EMAIL: Optional[str] = None
    MOD_REPLY_TO: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()