"""the submission object new_sub uses. with additional data
"""
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import AdminLog, SubmissionCategoryProposal

from app.shared.submission import SubmissionBase
from app.new_subs.submitter import SubmitterData

@dataclass
class NewSubmission(SubmissionBase):
    """one newly submitted paper, with everything the initial moderator email shows"""

    comments: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None

    #always fetched from the db by process_new_submission
    system_proposed_primary: Optional[str] = None

    #from the message when it has it. None until process_new_submission fetches it
    submitter_data: Optional[SubmitterData] = None


def fetch_auto_proposed_primary(submission_id: int) -> Optional[str]:
    """the primary category the system proposed for submission_id, or None.
    Any proposal_status counts. The proposal's own user_id is not used, since the system saves it wrongly.
    #TODO use proposal creator id when this is stored correctly in the db
    """
    with Session() as session:
        return session.scalar(
            select(SubmissionCategoryProposal.category)
            .join(AdminLog, AdminLog.id == SubmissionCategoryProposal.proposal_comment_id)
            .where(
                SubmissionCategoryProposal.submission_id == submission_id,
                SubmissionCategoryProposal.is_primary == 1,
                AdminLog.username == "system",
                AdminLog.logtext.like("Auto Proposed:%"),
            )
            .order_by(SubmissionCategoryProposal.proposal_id.desc())
            .limit(1)
        )
