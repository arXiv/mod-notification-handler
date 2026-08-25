"""category proposals on a submission. only unresolved ones are reported"""
import logging
from dataclasses import dataclass, field
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import SubmissionCategoryProposal

logger = logging.getLogger(__name__)

@dataclass
class Proposals:
    """the unresolved proposals on one submission"""
    primary: list[str] = field(default_factory=list)   
    secondary: list[str] = field(default_factory=list) 

    def __bool__(self) -> bool:
        return bool(self.primary or self.secondary)


def get_unresolved_proposals(submission_ids: set[int]) -> dict[int, Proposals]:
    """get unresolved proposals for submissions on the list"""
    if not submission_ids:
        return {}

    #fetch
    with Session() as session:
        rows = session.execute(
            select(
                SubmissionCategoryProposal.submission_id,
                SubmissionCategoryProposal.category,
                SubmissionCategoryProposal.is_primary,
            ).where(
                SubmissionCategoryProposal.submission_id.in_(submission_ids),
                SubmissionCategoryProposal.proposal_status == 0, #unresolved
            )
        ).all()

    #collect into dictionary
    by_sub: dict[int, Proposals] = {}
    for row in rows:
        entry = by_sub.setdefault(row.submission_id, Proposals())
        if row.is_primary:
            entry.primary.append(row.category)
        else:
            entry.secondary.append(row.category)

    #alphabetize
    for entry in by_sub.values():
        entry.primary.sort()
        entry.secondary.sort()

    return by_sub
