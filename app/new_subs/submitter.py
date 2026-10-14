"""whether the submitter is flagged, and whether this is their first submission"""
from pydantic import BaseModel
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Demographic


class SubmitterData(BaseModel):
    """the submitter facts the email warns about. rarely, the message carries them"""
    is_suspect: bool
    first_time_submitter: bool


def _fetch_is_suspect(user_id: int) -> bool:
    """flag_suspect from arXiv_demographics. a user with no row there is not flagged"""
    with Session() as session:
        flag = session.scalar(
            select(Demographic.flag_suspect).where(Demographic.user_id == user_id)
        )
    return bool(flag)


def fetch_submitter_data(user_id: int) -> SubmitterData:
    """the submitter data for user_id, from the db"""
    return SubmitterData(
        is_suspect=_fetch_is_suspect(user_id),
        first_time_submitter=False, #TODO query not written yet
    )
