from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CLASSIC_DB_URI: str
    ENV: str = 'LOCAL'

    #email related
    SEND_EMAILS: bool = False
    SMTP_PASSWORD: str 
    SMTP_HOST: str = "mailh.arxiv.org"
    SMTP_USER: str = "arxiv"
    MAIL_FROM: str = "e-prints@arxiv.org"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()