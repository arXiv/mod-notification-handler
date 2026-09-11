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


class ReportRenderError(Exception):
    """the digest could not be built. a bug in the report, so rerunning hits it again"""


def _subject() -> str:
    return f"Daily arXiv Moderator report {now_et().date().isoformat()}"


def send_digest(mod: DigestMod, submissions: list[OpenSubmission], to_email: str) -> bool:
    """render and send one moderator's digest. returns whether the relay accepted it

    Raises ReportRenderError when the report cannot be built, which no retry will fix.
    """
    try:
        body_text, body_html = render_report(mod, submissions)
    except Exception as exc:
        raise ReportRenderError(f"could not render the digest for {mod.header}") from exc

    try:
        return _send_with_retry(to_email, body_text, body_html)
    except Exception:
        logger.exception(f"failed to send digest for {mod.header} to {to_email}")
        return False


def _send_with_retry(to_email: str, body_text: str, body_html: str) -> bool:
    """send one digest, retrying potential transient relay failures
    Raises once the attempts are used up, or straight away for a failure retrying cannot fix.
    """
    for attempt in range(1, SEND_ATTEMPTS + 1):
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
            failure = exc
        except (smtplib.SMTPServerDisconnected, OSError) as exc:
            failure = exc

        if attempt == SEND_ATTEMPTS:
            raise failure #out of attempts, the last error is the one worth seeing
        logger.warning(f"relay problem sending to {to_email} ({failure}), retrying")
        time.sleep(RETRY_WAIT_SEC)
