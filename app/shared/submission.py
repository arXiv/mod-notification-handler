"""submission data fetching shared by all jobs"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Submission, SubmissionCategory

from app.shared.utils.formatting import build_category_string


@dataclass
class SubEmailData:
    submission_id: int
    title: str
    authors: str
    status: int
    submitter_name: str
    submitter_id: int
    submission_categories: str = ""
    submit_time: Optional[datetime] = None


def get_submission_info(submission_ids: set[int]) -> dict[int, SubEmailData]:
    """Fetch submission fields needed for email rendering. Returns only found rows."""
    if not submission_ids:
        return {}
    with Session() as session:
        #get general submission data
        rows = session.execute(
            select(
                Submission.submission_id,
                Submission.title,
                Submission.authors,
                Submission.status,
                Submission.submitter_name,
                Submission.submitter_id,
                Submission.submit_time,
            ).where(Submission.submission_id.in_(submission_ids))
        ).all()

        #get and consolidate category data
        cat_rows = session.execute(
            select(SubmissionCategory.submission_id, SubmissionCategory.category, SubmissionCategory.is_primary)
            .where(SubmissionCategory.submission_id.in_(submission_ids))
        ).all()

        cats_by_sub: dict[int, list[tuple[str, int]]] = {}
        for cr in cat_rows:
            cats_by_sub.setdefault(cr.submission_id, []).append((cr.category, cr.is_primary))

        return {
            row.submission_id: SubEmailData(
                submission_id=row.submission_id,
                title=row.title or "",
                authors=row.authors or "",
                status=row.status,
                submitter_name=row.submitter_name or "",
                submitter_id=row.submitter_id or 0,
                submission_categories=build_category_string(cats_by_sub.get(row.submission_id, [])),
                submit_time=row.submit_time,
            )
            for row in rows
        }
