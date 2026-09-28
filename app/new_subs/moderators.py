"""decides who gets a new_subs email
Job-specific flag rules: `no_email` blocks a send, and `no_reply_to` keeps a moderator out of
Reply-To.
"""
import logging

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.shared.moderators import (
    ToEmail,
    fetch_moderators,
    get_mod_emails,
    get_recipient_ids_for_categories,
)
from app.shared.submission import SubmissionBase

logger = logging.getLogger(__name__)


def get_moderators() -> tuple[dict[str, ToEmail], dict[str, ToEmail]]:
    """fetch mod data from db. process into who to email for categories"""

    all_cats: dict[str, ToEmail] = {}
    all_archives: dict[str, ToEmail] = {}

    for mod in fetch_moderators():
        # is this a category or archive entry
        is_category = bool(mod.category)
        store = all_cats if is_category else all_archives
        key = mod.category if is_category else mod.archive

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

    return all_archives, all_cats


def get_recipients(sub: SubmissionBase) -> tuple[list[str], list[str]]:
    """the addresses for one submission's email, as (to, reply_to)"""

    # only new categories emailed for crosses
    if sub.sub_type == "cross":
        notified = sub.new_cross_categories
    else:
        notified = {cat.category for cat in sub.categories}

    categories: set[Category] = set()
    #TODO also notify the moderators of any unresolved proposal
    for cat_id in notified:
        try:
            categories.add(CATEGORIES_ACTIVE[cat_id])
        except KeyError:
            logger.error(f"submission {sub.submission_id}: unknown category {cat_id}, skipping")

    archives, cats = get_moderators()
    per_cat, _ = get_recipient_ids_for_categories(categories, archives, cats)

    email_ids: set[int] = set()
    reply_ids: set[int] = set()
    for emails, replies in per_cat.values():
        email_ids.update(emails)
        reply_ids.update(replies)

    ids_to_contact = get_mod_emails(email_ids | reply_ids)
    missing = (email_ids | reply_ids) - ids_to_contact.keys()
    if missing:
        logger.error(f"submission {sub.submission_id}: no tapir_users row for moderator ids {missing}")

    to_emails = [ids_to_contact[uid].email for uid in email_ids if uid in ids_to_contact]
    reply_to = [ids_to_contact[uid].email for uid in reply_ids if uid in ids_to_contact]
    return to_emails, reply_to
