"""which submissions belong in the daily digest, and which section they land in"""
import logging

from arxiv.submission import statuses

from app.shared.submission import has_test_category
from app.daily_update.submissions import OpenSubmission

logger = logging.getLogger(__name__)

#types the digest reports on. Anything else is dropped, including withdrawals and journal refs
REPORTED_TYPES = frozenset({"new", "rep", "cross"})


def proposal_cats(sub: OpenSubmission) -> set[str]:
    """every category with an unresolved proposal on the submission, primary or secondary"""
    return set(sub.proposals.primary) | set(sub.proposals.secondary)


# ── which submissions to include ──────────────────────────────────────────────

def is_reported_type(sub: OpenSubmission) -> bool:
    """only certain types of submissions go to mods"""
    return sub.sub_type in REPORTED_TYPES


def is_unheld_replacement(sub: OpenSubmission) -> bool:
    """mods only see replacements on mod hold"""
    return sub.sub_type == "rep" and sub.status != statuses.ON_HOLD


def is_non_mod_hold(sub: OpenSubmission) -> bool:
    """on hold for anything but a moderator hold — an admin hold, or a legacy hold"""
    return sub.status == statuses.ON_HOLD and not sub.mod_hold


def report_on(submissions: list[OpenSubmission]) -> list[OpenSubmission]:
    """filter out all the submissions that shouldnt be included"""
    kept = [
        sub for sub in submissions
        if is_reported_type(sub)
        and not is_unheld_replacement(sub)
        and not is_non_mod_hold(sub)
        and not has_test_category(sub)
    ]
    logger.info(f"{len(kept)} of {len(submissions)} open submissions are correct type for daily update")
    return kept


# ── sorting submissions to moderators ──────────────────────

def get_subs_for_mod(
    categories: set[str], submissions: list[OpenSubmission]
) -> list[OpenSubmission]:
    """finds submissions that match a moderators categories"""
    theirs = []
    for sub in submissions:
        if sub.sub_type == "cross":
            notified_cats = sub.new_cross_categories #only new categories get shown crosses
        else:
            notified_cats = sub.category_ids
        
        notified_cats = notified_cats | proposal_cats(sub) #also notify proposed categories

        if notified_cats.intersection(categories): #find matches
            theirs.append(sub)

    return theirs
