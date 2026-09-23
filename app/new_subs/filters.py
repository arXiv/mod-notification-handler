"""the checks that decide whether a new submission is worth emailing moderators about
"""
import logging

from app.shared.submission import SubmissionBase

logger = logging.getLogger(__name__)


def notify_about(sub: SubmissionBase) -> bool:
    """should moderators be emailed about this submission at all"""
    #TODO the rules. candidates, by analogy with daily_update:
    #  - test categories
    #  - autoholds
    #  - submission types?
    return True
