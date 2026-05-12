"""email sending via Halon SMTP relay"""
import smtplib
import email.message
import email.utils
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_OVERRIDE_RECIPIENT = "test-colab-group@arxiv.org"


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    reply_to_emails: Optional[list[str]] = None,
) -> None:
    """Send a plain-text email via the Halon SMTP relay."""

    if not settings.SEND_EMAILS:
        logger.info(f"Email sending disabled. Would send to {to_emails}: {subject}")
        return

    redirect_header = f"[TEST REDIRECT]\nOriginal To: {', '.join(to_emails)}"
    if reply_to_emails:
        redirect_header += f"\nOriginal Reply-To: {', '.join(reply_to_emails)}"
    body = redirect_header + "\n\n" + body
    to_emails = [_OVERRIDE_RECIPIENT]
    reply_to_emails = None

    msg = email.message.EmailMessage()
    msg["Date"] = email.utils.format_datetime(email.utils.localtime())
    msg["Message-ID"] = email.utils.make_msgid()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    if reply_to_emails:
        msg["Reply-To"] = ", ".join(reply_to_emails)
    msg.set_content(body, cte="8bit")

    with smtplib.SMTP_SSL(host=settings.SMTP_HOST) as sess:
        sess.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        sess.send_message(
            msg,
            from_addr=settings.MAIL_FROM,
            to_addrs=to_emails,
            mail_options=("8bitmime",),
        )
    logger.info(f"Email sent to {to_emails}: {subject}")
