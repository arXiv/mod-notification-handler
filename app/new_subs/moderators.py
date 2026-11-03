"""decides who gets a new_subs email
Job-specific flag rules: `no_email` blocks a send, and `no_reply_to` keeps a moderator out of
Reply-To.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.shared.moderators import (
    ToEmail,
    fetch_moderators,
    get_mod_emails,
    get_recipient_ids_for_categories,
)
from app.shared.schema import UserContact
from app.new_subs.submission import NewSubmission

logger = logging.getLogger(__name__)


@dataclass
class ModeratorData:
    """everything get_recipients needs to know about moderators, as of fetched_at"""
    fetched_at: float #time.monotonic()
    archives: dict[str, ToEmail]
    categories: dict[str, ToEmail]
    contacts: dict[int, UserContact] #every moderator, by user id


#new_subs is a long-lived service, so this survives between messages
_moderators_cache: Optional[ModeratorData] = None


def get_moderators() -> ModeratorData:
    """the moderator data, refetched from the db after an hour"""
    global _moderators_cache
    now = time.monotonic()
    if _moderators_cache is None or now - _moderators_cache.fetched_at > 3600:
        _moderators_cache = _fetch_moderators(now)
    return _moderators_cache


def _fetch_moderators(fetched_at: float) -> ModeratorData:
    """fetch mod data from db. process into who to email for categories, and fetch each moderator's contact"""

    all_cats: dict[str, ToEmail] = {}
    all_archives: dict[str, ToEmail] = {}
    user_ids: set[int] = set()

    for mod in fetch_moderators():
        user_ids.add(mod.user_id)
        # is this a category or archive entry
        if mod.category:
            store = all_cats
            key = mod.category
        else:
            store = all_archives
            key = mod.archive

        entry: ToEmail = store.get(key, ToEmail())

        #email pref
        if mod.no_email:
            entry.dont_send_to.add(mod.user_id)
        else:
            entry.send_to.add(mod.user_id)

        # reply to pref
        if mod.no_reply_to:
            entry.dont_include_reply_to.add(mod.user_id)
        else:
            entry.include_reply_to.add(mod.user_id)

        store[key] = entry

    return ModeratorData(fetched_at, all_archives, all_cats, get_mod_emails(user_ids))


def get_recipients(sub: NewSubmission) -> tuple[list[str], list[str]]:
    """the addresses for one submission's email, as (to, reply_to)"""

    # only new categories emailed for crosses
    if sub.sub_type == "cross":
        notified = sub.new_cross_categories
    else:
        notified = {cat.category for cat in sub.categories}

    notified = notified | sub.unresolved_proposals.categories #also notify proposed categories

    categories: set[Category] = set()
    for cat_id in notified:
        try:
            categories.add(CATEGORIES_ACTIVE[cat_id])
        except KeyError:
            logger.error(f"submission {sub.submission_id}: unknown category {cat_id}, skipping")

    mods = get_moderators()
    per_cat, _ = get_recipient_ids_for_categories(categories, mods.archives, mods.categories)

    email_ids: set[int] = set()
    reply_ids: set[int] = set()
    for emails, replies in per_cat.values():
        email_ids.update(emails)
        reply_ids.update(replies)

    missing = (email_ids | reply_ids) - mods.contacts.keys()
    if missing:
        logger.error(f"submission {sub.submission_id}: no tapir_users row for moderator ids {missing}")

    to_emails = [mods.contacts[uid].email for uid in email_ids if uid in mods.contacts]
    reply_to = [mods.contacts[uid].email for uid in reply_ids if uid in mods.contacts]
    return to_emails, reply_to
