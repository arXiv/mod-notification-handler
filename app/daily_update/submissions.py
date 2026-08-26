"""the open moderation queue, and the extra fields a queue report needs"""
from dataclasses import dataclass, field
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Submission, SubmissionHoldReason
from arxiv.submission import statuses

from app.shared.proposals import Proposals, get_unresolved_proposals
from app.shared.submission import SubmissionBase, fetch_categories

OPEN_STATUSES = (statuses.SUBMITTED, statuses.ON_HOLD)
HOLD_MOD = "mod"

@dataclass
class OpenSubmission(SubmissionBase):
    """one submission awaiting moderation, with everything a queue report needs"""
    sub_type: str = "" #new/rep/cross/wdr/jref
    mod_hold: bool = False #indicates if submission is on (mod) hold
    proposals: Proposals = field(default_factory=Proposals)

    @property
    def new_cross_categories(self) -> set[str]:
        #rows not yet announced. On a cross these are the categories being requested
        return {cat.category for cat in self.categories if not cat.is_published}


def _fetch_mod_holds(session, submission_ids: set[int]) -> set[int]:
    """read arXiv_submission_hold_reason, keeping only the submissions on a moderator hold"""
    rows = session.execute(
        select(SubmissionHoldReason.submission_id)
        .where(SubmissionHoldReason.submission_id.in_(submission_ids))
        .where(SubmissionHoldReason.type == HOLD_MOD)
    ).all()
    return {row.submission_id for row in rows}


def get_open_submissions() -> list[OpenSubmission]:
    """every submission still awaiting moderation, newest first. no product filtering — see
    filters.py"""

    with Session() as session:
        rows = session.execute(
            select(
                Submission.submission_id,
                Submission.title,
                Submission.authors,
                Submission.status,
                Submission.submitter_name,
                Submission.submitter_id,
                Submission.submit_time,
                Submission.type,
            )
            .where(Submission.status.in_(OPEN_STATUSES))
            .order_by(Submission.submit_time.desc())
        ).all()

        if not rows:
            return []

        ids = {row.submission_id for row in rows}
        cats_by_sub = fetch_categories(session, ids)
        mod_holds = _fetch_mod_holds(session, ids)
        proposals = get_unresolved_proposals(session, ids)

    submissions: list[OpenSubmission] = []
    for row in rows:
        submissions.append(OpenSubmission(
            submission_id=row.submission_id,
            title=row.title or "",
            authors=row.authors or "",
            status=row.status,
            submitter_name=row.submitter_name or "",
            submitter_id=row.submitter_id or 0,
            submit_time=row.submit_time,
            sub_type=row.type or "",
            categories=cats_by_sub.get(row.submission_id, []),
            mod_hold=row.submission_id in mod_holds,
            proposals=proposals.get(row.submission_id, Proposals()),
        ))

    return submissions
