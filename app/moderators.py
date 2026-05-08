"""handles getting data from the database"""
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import select

from arxiv.taxonomy.category import Category
from arxiv.db import Session
from arxiv.db.models import t_arXiv_moderators

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

    #add specific category moderators
    email.update(all_cats[category.id].send_to)
    reply_to.update(all_cats[category.id].include_reply_to)

    #add archive mods unless they have specifically declined
    also_email=all_archives[category.in_archive].send_to - all_cats[category.id].dont_send_to
    email.update(also_email)
    also_reply_to = all_archives[category.in_archive].include_reply_to - all_cats[category.id].dont_include_reply_to
    also_reply_to.update(also_reply_to)

    return email, reply_to
