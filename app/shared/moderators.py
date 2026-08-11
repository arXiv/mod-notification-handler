"""handles getting moderator data from the database

Deciding who actually gets emailed is job-specific — each job has its own
rules about which email preference flags block a send, so each one owns a
moderators.py that turns fetch_moderators() into ToEmail dicts. Everything
downstream of those dicts (who_to_email and friends) is shared.
"""
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE
from arxiv.db import Session
from arxiv.db.models import t_arXiv_moderators, TapirUser, TapirNickname

from app.shared.schema import UserContact
from app.shared.utils.taxonomy import ALIAS_BY_CANONICAL

class Moderator(BaseModel):
    user_id:int
    archive: str
    category: Optional[str]
    no_email: bool
    no_web_email:bool
    no_reply_to: bool
    daily_update: bool

class ToEmail(BaseModel):
    send_to: set[int] = Field(default_factory=set)# list of userids to send the email to
    include_reply_to: set[int] = Field(default_factory=set) #list of userids to include in the reply to part of the email
    dont_send_to: set[int] = Field(default_factory=set)# list of userids to NOT send the email to
    dont_include_reply_to: set[int] = Field(default_factory=set) #list of userids to NOT include in the reply to part of the email

def _build_category_name(row) -> Optional[str]:
    """creates proper category name from table data"""
    subject_class = row["subject_class"]
    return f"{row['archive']}.{subject_class}" if subject_class else None

def fetch_moderators() -> list[Moderator]:
    """fetch all moderator rows from the db. no filtering — each job decides what the flags mean"""

    with Session() as session:
        result = session.execute(select(t_arXiv_moderators))
        rows = result.mappings().all()

    return [
        Moderator(
            user_id=row["user_id"],
            archive=row["archive"],
            category=_build_category_name(row),
            no_email=bool(row["no_email"]),
            no_web_email=bool(row["no_web_email"]),
            no_reply_to=bool(row["no_reply_to"]),
            daily_update=bool(row["daily_update"]),
        )
        for row in rows
    ]

def who_to_email(category: Category, all_archives: dict[str, ToEmail], all_cats: dict[str, ToEmail])-> tuple[set[int], set[int]]:
    """determines who to include in an email for a given set of categories"""

    email: set[int] = set()
    reply_to: set[int] = set()
    rolling_dont_email: set[int] = set()
    rolling_dont_reply: set[int] = set()

    cat_entry = all_cats.get(category.id, ToEmail())
    archive_entry = all_archives.get(category.in_archive, ToEmail())

    #dont forget alaises
    alias_id = ALIAS_BY_CANONICAL.get(category.id)
    if alias_id:
        alias=CATEGORIES_ACTIVE[alias_id]
        alias_cat_entry = all_cats.get(alias_id, ToEmail())
        alias_archive_entry = all_archives.get(alias.in_archive, ToEmail())

    # factory in email preferences
    #priority: named category > alias category > named archive > alias archive
    #each lower-priority group excludes anyone who opted out at a higher-priority level

    #named category moderators
    email.update(cat_entry.send_to)
    reply_to.update(cat_entry.include_reply_to)
    rolling_dont_email.update(cat_entry.dont_send_to)
    rolling_dont_reply.update(cat_entry.dont_include_reply_to)

    #alias category moderators
    if alias_id:
        email.update(alias_cat_entry.send_to - rolling_dont_email)
        reply_to.update(alias_cat_entry.include_reply_to - rolling_dont_reply)
        rolling_dont_email.update(alias_cat_entry.dont_send_to)
        rolling_dont_reply.update(alias_cat_entry.dont_include_reply_to)

    #named archive moderators
    email.update(archive_entry.send_to - rolling_dont_email)
    reply_to.update(archive_entry.include_reply_to - rolling_dont_reply)
    rolling_dont_email.update(archive_entry.dont_send_to)
    rolling_dont_reply.update(archive_entry.dont_include_reply_to)

    #alias archive moderators
    if alias_id:
        email.update(alias_archive_entry.send_to - rolling_dont_email)
        reply_to.update(alias_archive_entry.include_reply_to - rolling_dont_reply)

    return email, reply_to

def get_recipient_ids_for_categories(categories: set[Category], all_archives: dict[str, ToEmail], all_cats: dict[str, ToEmail],
) -> tuple[dict[str, tuple[set[int], set[int]]], set[int]]:
    """Returns {category.id: (email_ids, reply_ids)} and all unique user IDs across all categories."""
    per_cat: dict[str, tuple[set[int], set[int]]] = {}
    all_user_ids: set[int] = set()
    for cat in categories:
        e, r = who_to_email(cat, all_archives, all_cats)
        per_cat[cat.id] = (e, r)
        all_user_ids.update(e | r)
    return per_cat, all_user_ids

def get_mod_emails(user_ids: set[int]) -> dict[int, UserContact]:
    """Returns {user_id: UserContact} with email and primary nickname for the given user_ids."""
    if not user_ids:
        return {}
    with Session() as session:
        rows = session.execute(
            select(TapirUser.user_id, TapirUser.email, TapirUser.first_name, TapirUser.last_name, TapirNickname.nickname)
            .outerjoin(
                TapirNickname,
                (TapirNickname.user_id == TapirUser.user_id),
            )
            .where(TapirUser.user_id.in_(user_ids))
        )
        return {
            row.user_id: UserContact(
                email=row.email,
                nickname=row.nickname or "",
                first_name=row.first_name or "",
                last_name=row.last_name or "",
            )
            for row in rows
        }
