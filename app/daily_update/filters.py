"""which submissions belong in the daily digest, and which section they land in"""
import logging

from arxiv.submission import statuses
from arxiv.taxonomy.definitions import CATEGORIES

from app.daily_update.submissions import OpenSubmission

logger = logging.getLogger(__name__)

#types the digest reports on. Anything else is dropped, including withdrawals and journal refs
REPORTED_TYPES = frozenset({"new", "rep", "cross"})

#the test archive isn't real content; test.* categories are not in the active taxonomy
TEST_ARCHIVE = "test"

def proposal_cats(sub: OpenSubmission) -> set[str]:
    """every category with an unresolved proposal on the submission, primary or secondary"""
    return set(sub.proposals.primary) | set(sub.proposals.secondary)


def _category_ids(sub: OpenSubmission) -> set[str]:
    """every category on the submission, primary and secondary together"""
    ids = set(sub.secondary_categories)
    if sub.primary_category:
        ids.add(sub.primary_category)
    return ids


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


def has_test_category(sub: OpenSubmission) -> bool:
    """any category, primary or secondary, is in the test archive"""
    for cat_id in _category_ids(sub):
        category = CATEGORIES.get(cat_id)
        #categories missing from the taxonomy just never match a moderator, so they pass here
        if category is not None and category.in_archive == TEST_ARCHIVE:
            return True
    return False


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
            notified_cats = _category_ids(sub)
        
        notified_cats = notified_cats | proposal_cats(sub) #also notify proposed categories

        if notified_cats.intersection(categories): #find matches
            theirs.append(sub)

    return theirs
