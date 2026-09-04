"""submission data fetching shared by all jobs"""
from datetime import datetime, timezone
from functools import cached_property
from typing import Optional
from dataclasses import dataclass, field
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Submission, SubmissionCategory

from app.shared.utils.taxonomy import ALIAS_BY_CANONICAL

def as_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """attach the zone a submission timestamp is stored in

    The columns are naive DATETIME holding UTC. Left naive, astimezone() downstream would read
    them in whatever zone the machine happens to be in.
    """
    if dt is not None and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass(frozen=True)
class SubmissionCat:
    """one arXiv_submission_category row"""
    category: str
    is_published: bool #already announced under this category
    is_primary: bool

def fetch_categories(session, submission_ids: set[int]) -> dict[int, list[SubmissionCat]]:
    """read arXiv_submission_category, one list of rows per submission"""
    rows = session.execute(
        select(
            SubmissionCategory.submission_id,
            SubmissionCategory.category,
            SubmissionCategory.is_primary,
            SubmissionCategory.is_published,
        ).where(SubmissionCategory.submission_id.in_(submission_ids))
    ).all()

    cats_by_sub: dict[int, list[SubmissionCat]] = {}
    for row in rows:
        cats_by_sub.setdefault(row.submission_id, []).append(SubmissionCat(
            category=row.category,
            is_published=bool(row.is_published),
            is_primary=bool(row.is_primary),
        ))
    return cats_by_sub


def split_categories(cats: list[SubmissionCat]) -> tuple[Optional[str], list[str]]:
    """Split category rows into (primary, sorted secondaries). primary is None when the
    submission has no primary row."""
    primary: Optional[str] = None
    secondaries: set[str] = set()
    for cat in cats:
        if cat.is_primary:
            primary = cat.category
        else:
            secondaries.add(cat.category)
        #catch aliases
        if cat.category in ALIAS_BY_CANONICAL:
            secondaries.add(ALIAS_BY_CANONICAL[cat.category])
    return primary, sorted(secondaries)


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
    categories: list[SubmissionCat] = field(default_factory=list)

    @property
    def primary_category(self) -> Optional[str]:
        """None when the submission has no primary row"""
        return self._split[0]

    @property
    def secondary_categories(self) -> list[str]:
        """alphabetized, aliases included"""
        return self._split[1]

    @cached_property
    def _split(self) -> tuple[Optional[str], list[str]]:
        return split_categories(self.categories)

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

        cats_by_sub = fetch_categories(session, submission_ids)

        def build(row):
            return SubEmailData(
                submission_id=row.submission_id,
                title=row.title or "",
                authors=row.authors or "",
                status=row.status,
                submitter_name=row.submitter_name or "",
                submitter_id=row.submitter_id or 0,
                submit_time=as_utc(row.submit_time),
                categories=cats_by_sub.get(row.submission_id, []),
            )

        return {row.submission_id: build(row) for row in rows}
