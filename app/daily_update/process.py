"""runs the daily digest job: gather, match, hand each moderator's email off to be sent"""
import logging

from app.shared.moderators import get_mod_emails

from app.daily_update.digest_email import send_digest
from app.daily_update.filters import get_subs_for_mod, report_on
from app.daily_update.moderators import get_digest_recipients
from app.daily_update.submissions import get_open_submissions

logger = logging.getLogger(__name__)


def send_daily_reports() -> None:
    """send every daily digest for today"""

    #gather info
    recipients = get_digest_recipients() #all mods who get daily update
    if not recipients:
        logger.info("No moderators want a daily digest, nothing to send")
        return

    all_open = get_open_submissions() #all submissions
    reportable = report_on(all_open) # all qualifying submissions
    ids_to_contact = get_mod_emails(set(recipients.keys())) #contact info for daily update mods

    #build emails for each mod
    sent = 0
    for mod in recipients.values():
        contact = ids_to_contact.get(mod.user_id)
        if contact is None:
            logger.error(f"moderator {mod.user_id}: no tapir_users row, skipping their digest")
            continue

        theirs = get_subs_for_mod(mod.categories, reportable)
        #sent even when empty
        if send_digest(mod, theirs, contact.email):
            sent += 1

    # report success
    logger.info(
        f"Done. {sent} emails sent to moderators.")
