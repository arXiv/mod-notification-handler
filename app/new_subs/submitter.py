"""whether the submitter is flagged, and whether this is their first submission"""
from pydantic import BaseModel
from sqlalchemy import exists, select

from arxiv.db import Session
from arxiv.db.models import Demographic, Submission
from arxiv.submission.statuses import DELETED_ON_HOLD, DELETED_PUBLISHED, DELETED_REMOVED, PUBLISHED, PUBLISHING, REMOVED


class SubmitterData(BaseModel):
    """the submitter facts the email warns about. rarely, the message carries them"""
    is_suspect: bool
    first_time_submitter: bool


def fetch_submitter_data(user_id: int) -> SubmitterData:
    """the submitter data for user_id"""
    flag_suspect = (
        select(Demographic.flag_suspect)
        .where(Demographic.user_id == user_id)
        .scalar_subquery()
    )
    #follows same rules as modapi
    submitted_before = exists().where(
        Submission.submitter_id == user_id,
        Submission.type.in_(["new", "rep"]),
        Submission.status.in_([
            PUBLISHED, PUBLISHING, REMOVED, DELETED_ON_HOLD, DELETED_PUBLISHED, DELETED_REMOVED,
        ]),
    )

    with Session() as session:
        row = session.execute(select(flag_suspect, submitted_before)).one()

    #a user with no demographics row is not flagged
    return SubmitterData(is_suspect=bool(row[0]), first_time_submitter=not row[1])
