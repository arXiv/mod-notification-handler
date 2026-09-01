"""assembles and sends one moderator's digest email"""
import logging
import smtplib
import time

from app.shared.utils.email import send_email
from app.shared.utils.formatting import now_et

from app.daily_update.report_content import render_report
from app.daily_update.moderators import DigestMod
from app.daily_update.submissions import OpenSubmission

logger = logging.getLogger(__name__)

# retry config for individual mod emails
SEND_ATTEMPTS = 3
RETRY_WAIT_SEC = 10


def _subject() -> str:
    return f"Daily arXiv Moderator report {now_et().date().isoformat()}"


def send_digest(mod: DigestMod, submissions: list[OpenSubmission], to_email: str) -> bool:
    """render and send one moderator's digest. returns whether the relay accepted it"""
    try:
        body_text, body_html = render_report(mod, submissions)
    except Exception:
        logger.exception(f"failed to render digest for {mod.header} to {to_email}, skipping")
        return False

    try:
        return _send_with_retry(to_email, body_text, body_html)
    except Exception:
        logger.exception(f"failed to send digest for {mod.header} to {to_email}")
        return False


def _send_with_retry(to_email: str, body_text: str, body_html: str) -> bool:
    """send one digest, retrying potential transient relay failures
    Raises once the attempts are used up, or straight away for a failure retrying cannot fix.
    """
    last_failure = None
    for _ in range(SEND_ATTEMPTS):
        if last_failure is not None: #dont wait the first time
            logger.warning(
                f"relay problem sending to {to_email} ({last_failure}), retrying"
            )
            time.sleep(RETRY_WAIT_SEC)

        try:
            #no submission_id: a digest isn't about one submission, so no threading headers
            return send_email(
                to_emails=[to_email],
                subject=_subject(),
                body=body_text,
                html_body=body_html,
            )
        except smtplib.SMTPAuthenticationError:
            raise #bad credentials. retrying will not help and may lock the account
        except smtplib.SMTPResponseException as exc:
            if not 400 <= exc.smtp_code < 500:
                raise #5xx is the relay saying no permanently
            last_failure = exc
        except (smtplib.SMTPServerDisconnected, OSError) as exc:
            last_failure = exc

    raise last_failure #give up on attempts
