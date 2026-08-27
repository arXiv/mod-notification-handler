"""startup checks shared by all jobs"""
import logging

from app.shared.config import settings

logger = logging.getLogger(__name__)


def email_config_ok() -> bool:
    """fail fast on email misconfiguration before doing any work. False means the job should exit"""
    if settings.SEND_EMAILS:
        if settings.REDIRECT_EMAILS and not settings.REDIRECT_RECIPIENT:
            logger.error("SEND_EMAILS=True and REDIRECT_EMAILS=True but REDIRECT_RECIPIENT is not set — exiting")
            return False
        if not settings.REDIRECT_EMAILS and settings.ENV != "PRODUCTION":
            logger.error("SEND_EMAILS=True and REDIRECT_EMAILS=False but ENV is not PRODUCTION — exiting")
            return False
        if settings.REDIRECT_EMAILS:
            logger.info(f"REDIRECT_EMAILS active — all emails → {settings.REDIRECT_RECIPIENT}")
    elif settings.ENV == "PRODUCTION":
        logger.warning("SEND_EMAILS=False in PRODUCTION — messages will be acked without sending email")
    return True
