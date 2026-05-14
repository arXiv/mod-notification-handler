"""handles getting data from the database"""
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select

from arxiv.taxonomy.category import Category
from arxiv.db import Session
from arxiv.db.models import t_arXiv_moderators, TapirUser, TapirNickname

from app.schema import UserContact

class Moderator(BaseModel):
    user_id:int
    archive: str
    category: Optional[str]
    no_email: bool
    no_web_email:bool
    no_reply_to: bool

class ToEmail(BaseModel):
    send_to: set[int] = Field(default_factory=set)# list of userids to send the email to
    include_reply_to: set[int] = Field(default_factory=set) #list of userids to include in the reply to part of the email
    dont_send_to: set[int] = Field(default_factory=set)# list of userids to NOT send the email to
    dont_include_reply_to: set[int] = Field(default_factory=set) #list of userids to NOT include in the reply to part of the email

def _build_category_name(row) -> Optional[str]:
    """creates proper category name from table data"""
    subject_class = row["subject_class"]
    return f"{row['archive']}.{subject_class}" if subject_class else None

def get_all_moderators() -> tuple [dict[str, ToEmail], dict[str, ToEmail]]:
    """fetch mod data from db. process into who to email for categories"""

    #fetch data
    with Session() as session:
        result = session.execute(select(t_arXiv_moderators))
        rows = result.mappings().all()
     
    moderators = [
        Moderator(
            user_id=row["user_id"],
            archive=row["archive"],
            category=_build_category_name(row),
            no_email=bool(row["no_email"]),
            no_web_email=bool(row["no_web_email"]),
            no_reply_to=bool(row["no_reply_to"]),
        )
        for row in rows
    ]

    #who should get emailed
    all_cats: dict[str, ToEmail] ={}
    all_archives: dict[str, ToEmail] ={}
    
    for mod in moderators:
        # is this a category or archive entry
        is_category = bool(mod.category)
        store = all_cats if is_category else all_archives
        key = mod.category if is_category else mod.archive

        entry: ToEmail=store.get(key, ToEmail())

        #email pref
        if mod.no_email or mod.no_web_email:
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

def who_to_email(category: Category, all_archives: dict[str, ToEmail], all_cats: dict[str, ToEmail])-> tuple[set[int], set[int]]:
    """determines who to include in an email for a given set of categories"""

    email: set[int] = set()
    reply_to: set[int] = set()

    cat_entry = all_cats.get(category.id, ToEmail())
    archive_entry = all_archives.get(category.in_archive, ToEmail())

    #add specific category moderators
    email.update(cat_entry.send_to)
    reply_to.update(cat_entry.include_reply_to)

    #add archive mods unless they have specifically declined
    email.update(archive_entry.send_to - cat_entry.dont_send_to)
    reply_to.update(archive_entry.include_reply_to - cat_entry.dont_include_reply_to)

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
