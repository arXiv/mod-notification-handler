"""handles one new submission notification

One message is one submission is one email. Nothing here retries or gives up: the work
either finishes or raises, and Pub/Sub redelivers what wasn't acked.
"""
import logging

from app.shared.config import settings
from app.shared.submission import SubmissionBase
from app.shared.utils.email import send_email

from app.new_subs.email_content import render_email
from app.new_subs.filters import notify_about
from app.new_subs.moderators import get_recipients

logger = logging.getLogger(__name__)


def process_new_submission(sub: SubmissionBase) -> None:
    """check, build, send. returning means the message is done with, however it ended.
    Raises instead of returning when the work should be tried again on redelivery.
    """

    #should anyone hear about it
    if not notify_about(sub):
        logger.info(f"submission {sub.submission_id}: no notification needed")
        return #ack, no email should be sent

    #who hears about it
    to_emails, reply_to_emails = get_recipients(sub)
    if not to_emails:
        logger.info(f"submission {sub.submission_id}: no moderators to email")
        return #ack, nobody to email

    #build and send
    body_text, body_html = render_email(sub)
    #TODO subject line not decided
    submitter = sub.submitter_name or f"user {sub.submitter_id}"
    subject = f"New arXiv submission submit/{sub.submission_id} to {sub.subject_categories} by {submitter}"
    accepted = send_email(
        to_emails=to_emails,
        subject=subject,
        body=body_text,
        html_body=body_html,
        submission_id=sub.submission_id,
        reply_to_emails=reply_to_emails,
    )

    #check if everyone refused
    if not accepted and settings.SEND_EMAILS:
        logger.error(f"submission {sub.submission_id}: relay accepted no recipients")
        return # cant retry recipients refusing
