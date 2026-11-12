"""the checks that decide whether a new submission is worth emailing moderators about"""
import logging

from arxiv.submission import statuses

from app.shared.submission import SubmissionBase, has_test_category

logger = logging.getLogger(__name__)

#types moderators hear about. anything else is dropped, withdrawals and journal refs included
NOTIFIED_TYPES = frozenset({"new", "rep", "cross"})


def is_notified_type(sub: SubmissionBase) -> bool:
    """only certain types of submission are worth an email"""
    return sub.sub_type in NOTIFIED_TYPES


def is_on_auto_hold(sub: SubmissionBase) -> bool:
    """held automatically, so there is nothing for a moderator to act on yet. and authold submissions will be notified about later
    """
    if not sub.auto_hold:
        return False
    if sub.status != statuses.ON_HOLD:
        logger.warning(
            f"submission {sub.submission_id}: auto_hold set but status is {sub.status}, not on hold"
        )
        return False
    return True


def notify_about(sub: SubmissionBase) -> bool:
    """should moderators be emailed about this submission at all"""
    return (
        is_notified_type(sub)
        and not is_on_auto_hold(sub)
        and not has_test_category(sub)
    )
