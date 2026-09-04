"""runs the daily digest job: gather, match, hand each moderator's email off to be sent"""
import logging

from app.shared.config import settings
from app.shared.moderators import get_mod_emails

from app.daily_update import announce
from app.daily_update.digest_email import send_digest
from app.daily_update.filters import get_subs_for_mod, report_on
from app.daily_update.moderators import get_digest_recipients
from app.daily_update.submissions import get_open_submissions

logger = logging.getLogger(__name__)

GIVE_UP_AFTER = 5 #seperate mods unemailable in a row


def send_daily_reports() -> None:
    """send every daily digest for today"""

    #gather info
    recipients = get_digest_recipients() #all mods who get daily update
    if not recipients:
        logger.info("No moderators want a daily digest, nothing to send")
        return

    #fetched once, up front: every digest reuses the cached value
    announce.next_announce_time()

    all_open = get_open_submissions() #all submissions
    reportable = report_on(all_open) # all qualifying submissions
    ids_to_contact = get_mod_emails(set(recipients.keys())) #contact info for daily update mods

    #build emails for each mod.
    sent = 0
    failed = 0
    for mod in recipients.values():
        #build
        contact = ids_to_contact.get(mod.user_id)
        if contact is None:
            logger.error(f"moderator {mod.user_id}: no tapir_users row, skipping their digest")
            continue
        theirs = get_subs_for_mod(mod.categories, reportable)

        #send even when empty
        if send_digest(mod, theirs, contact.email):
            sent += 1
        else:
            failed += 1
            # if several fail at start give up and fail the job 
            if settings.SEND_EMAILS and sent == 0 and failed >= GIVE_UP_AFTER:
                raise RuntimeError(
                    f"{failed} digests failed and none have sent, giving up so the job retries"
                )

    #catch complete failure but few attempts
    if settings.SEND_EMAILS and sent == 0:
        raise RuntimeError(f"no digests reached any of {len(recipients)} moderators")

    # report success
    logger.info(f"Done. {sent} of {len(recipients)} emails sent to moderators.")
    if settings.SEND_EMAILS and sent != len(recipients):
        logger.warning(f"{len(recipients) - sent} moderators did not get a digest today")
