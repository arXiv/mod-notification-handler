from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    CLASSIC_DB_URI: str = "sqlite:///:memory:"
    ENV: str = 'LOCAL'

    LOG_LEVEL: str = "INFO"

    #configured the pubsub subscription notifications are pulled from
    GCP_PROJECT_ID: str = "arxiv-development"
    PUBSUB_SUBSCRIPTION_ID: str = "mod-notification-handler"
    PUBSUB_BATCH_SIZE: int = 300
    PUBSUB_MAX_PULL_SEC: int = 60

    #email configuration
    MAIL_FROM: str = "e-prints@arxiv.org" #address emails are sent from
    ARCHIVAL_EMAIL: Optional[str] = None #an archival address that recieves a copy of every email
    MOD_REPLY_TO: Optional[str] = None #the moderator support email to be included in the reply to of every email
    HALON_CREDS: str = "smtps://user:pass@host:port" 

    #email enabling and control
    """true: emails can be sent at all, false: no email will ever be sent (but messages will be acked)"""
    SEND_EMAILS: bool = False
    """if true redirect all emails from where they would have gone to a specified recipient"""
    REDIRECT_EMAILS: bool = True
    REDIRECT_RECIPIENT: Optional[str] = None #single email to recieve all redirected emails



    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

settings = Settings()