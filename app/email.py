"""email sending via Halon SMTP relay"""
import smtplib
import email.message
from email.utils import format_datetime, localtime, make_msgid
from urllib.parse import urlparse
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

_OVERRIDE_RECIPIENT = "test-colab-group@arxiv.org"


def send_email(
    to_emails: list[str],
    subject: str,
    body: str,
    html_body: str,
    reply_to_emails: Optional[list[str]] = None,
) -> None:
    """Send a plain-text and HTML email via the Halon SMTP relay."""

    if not settings.SEND_EMAILS:
        logger.info(f"Email sending disabled. Would send to {to_emails}: {subject}")
        return

    redirect_header = f"[TEST REDIRECT]\nOriginal To: {', '.join(to_emails)}"
    if reply_to_emails:
        redirect_header += f"\nOriginal Reply-To: {', '.join(reply_to_emails)}"
    body = redirect_header + "\n\n" + body
    html_body = redirect_header.replace("\n", "<br>\n") + "<br><br>\n" + html_body
    to_emails = [_OVERRIDE_RECIPIENT]
    reply_to_emails = []

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

    creds = urlparse(settings.HALON_CREDS)
    with smtplib.SMTP_SSL(host=creds.hostname, port=creds.port) as sess:
        sess.login(creds.username, creds.password)
        sess.send_message(
            msg,
            from_addr=settings.MAIL_FROM,
            to_addrs=to_emails,
            mail_options=("8bitmime",),
        )
    logger.info(f"Email sent to {to_emails}: {subject}")
