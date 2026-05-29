"""email sending via Halon SMTP relay"""
import smtplib
import email.message
from email.utils import format_datetime, localtime, make_msgid
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    html_body: str,
    reply_to_emails: Optional[list[str]] = None,
) -> None:
    """Send a plain-text and HTML email via the Halon SMTP relay."""

    reply_to_emails = (reply_to_emails or []) + ([settings.MOD_REPLY_TO] if settings.MOD_REPLY_TO else [])
    bcc_emails: list[str] = [settings.ARCHIVAL_EMAIL] if settings.ARCHIVAL_EMAIL else []

    if not settings.SEND_EMAILS:
        logger.info(f"Email sending disabled. Would send to {to_emails}: {subject}")
        return

    # redirect emails while under development
    if not settings.REDIRECT_RECIPIENT:
        logger.error("REDIRECT_RECIPIENT not set — refusing to send to avoid misdirected email")
        return

    redirect_header = f"[TEST REDIRECT]\nOriginal To: {', '.join(to_emails)}"
    if reply_to_emails:
        redirect_header += f"\nOriginal Reply-To: {', '.join(reply_to_emails)}"
    if bcc_emails:
        redirect_header += f"\nOriginal Bcc: {', '.join(bcc_emails)}"
    body = redirect_header + "\n\n" + body
    html_body = redirect_header.replace("\n", "<br>\n") + "<br><br>\n" + html_body
    to_emails = [settings.REDIRECT_RECIPIENT]
    reply_to_emails = []
    bcc_emails = []

    #build email
    msg = email.message.EmailMessage()
    msg["Date"] = format_datetime(localtime())
    msg["Message-ID"] = make_msgid()
    msg["From"] = settings.MAIL_FROM
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    if reply_to_emails:
        msg["Reply-To"] = ", ".join(reply_to_emails)
    msg.set_content(body, cte="8bit")
    msg.add_alternative(html_body, subtype="html")

    with smtplib.SMTP_SSL(host=settings.SMTP_HOST) as sess:
        sess.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        sess.send_message(
            msg,
            from_addr=settings.MAIL_FROM,
            to_addrs=to_emails + bcc_emails,
            mail_options=("8bitmime",),
        )
    logger.debug(f"Email sent to {to_emails + bcc_emails}: {subject}")
