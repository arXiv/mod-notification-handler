"""submission data fetching shared by all jobs"""
from datetime import datetime
from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Submission, SubmissionCategory

from app.shared.utils.formatting import split_categories


@dataclass
class SubmissionBase:
    """the submission fields every job needs"""
    submission_id: int
    title: str
    authors: str
    status: int
    submitter_name: str
    submitter_id: int
    submit_time: Optional[datetime] = None
    primary_category: Optional[str] = None 
    secondary_categories: list[str] = field(default_factory=list) #alphabetized, aliases included

    @property
    def submission_categories(self) -> str:
        """primary then secondaries as one string, 'no primary' standing in for a missing one"""
        return " ".join([self.primary_category or "no primary"] + self.secondary_categories)

    @property
    def subject_categories(self) -> str:
        """same list with '-' for a missing primary. subject lines have always read this way"""
        return " ".join([self.primary_category or "-"] + self.secondary_categories)


@dataclass
class SubEmailData(SubmissionBase):
    """a submission an action happened on. its status can be anything by render time"""
    #holding onto in case action emails get bonus features

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

        def build(row):
            primary, secondaries = split_categories(cats_by_sub.get(row.submission_id, []))
            return SubEmailData(
                submission_id=row.submission_id,
                title=row.title or "",
                authors=row.authors or "",
                status=row.status,
                submitter_name=row.submitter_name or "",
                submitter_id=row.submitter_id or 0,
                submit_time=row.submit_time,
                primary_category=primary,
                secondary_categories=secondaries,
            )

        return {row.submission_id: build(row) for row in rows}
