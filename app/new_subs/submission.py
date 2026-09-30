"""the submission object new_sub uses. with additional data
"""
from dataclasses import dataclass
from typing import Optional

from app.shared.submission import SubmissionBase

@dataclass
class NewSubmission(SubmissionBase):
    """one newly submitted paper, with everything the initial moderator email shows"""

    comments: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None

    #TODO no source yet
    system_proposed_primary: Optional[str] = None

    #TODO no source yet
    first_time_submitter: bool = False
    flagged_submitter: bool = False
