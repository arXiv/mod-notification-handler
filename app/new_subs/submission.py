"""the submission object new_sub uses. with additional data
"""
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import AdminLog, SubmissionCategoryProposal

from app.shared.proposals import Proposals
from app.shared.submission import SubmissionBase
from app.new_subs.submitter import SubmitterData

@dataclass
class NewSubmission(SubmissionBase):
    """one newly submitted paper, with everything the initial moderator email shows"""

    comments: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None

    system_proposed_primary: Optional[str] = None
    unresolved_proposals: Proposals = field(default_factory=Proposals)

    #from the message when it has it. None until process_new_submission fetches it
    submitter_data: Optional[SubmitterData] = None

   


def fill_proposal_fields(sub: NewSubmission) -> None:
    """sets the unresolved proposals, and the primary the system proposed (None if none).
    The system's primary counts at any proposal_status. The proposal's own user_id is not used, since the system saves it wrongly.
    #TODO use proposal creator id when this is stored correctly in the db
    """
    #every proposal, latest first, with the username and text of its admin log comment
    with Session() as session:
        rows = session.execute(
            select(
                SubmissionCategoryProposal.category,
                SubmissionCategoryProposal.is_primary,
                SubmissionCategoryProposal.proposal_status,
                AdminLog.username,
                AdminLog.logtext,
            )
            .outerjoin(AdminLog, AdminLog.id == SubmissionCategoryProposal.proposal_comment_id)
            .where(SubmissionCategoryProposal.submission_id == sub.submission_id)
            .order_by(SubmissionCategoryProposal.proposal_id.desc())
        ).all()

    for row in rows:
        #get unresolved props
        if row.proposal_status == 0:
            if row.is_primary:
                sub.unresolved_proposals.primary.append(row.category)
            else:
                sub.unresolved_proposals.secondary.append(row.category)
                
        #check for system proposed primary        
        #rows are latest first, so the first match is the latest
        if sub.system_proposed_primary is None and row.is_primary and row.username == "system" and (row.logtext or "").startswith("Auto Proposed:"):
            sub.system_proposed_primary = row.category
