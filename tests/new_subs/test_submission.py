"""tests for reading a submission's proposals from the db"""
from typing import Optional

import pytest

from app.new_subs.submission import NewSubmission, fill_proposal_fields
from app.shared.proposals import Proposals


def _filled(submission_id: int) -> tuple[Proposals, Optional[str]]:
    """the proposal fields after reading submission_id's proposals"""
    sub = NewSubmission(
        submission_id=submission_id, title="A Title", authors="An Author", status=1,
        submitter_name="Pippin Otter", submitter_id=246234,
    )
    fill_proposal_fields(sub)
    return sub.unresolved_proposals, sub.system_proposed_primary


@pytest.mark.usefixtures("db_session")
def test_the_system_proposal_is_unresolved_and_the_auto_proposed_primary():
    assert _filled(8242408) == (Proposals(primary=["cs.CL"]), "cs.CL")


@pytest.mark.usefixtures("db_session")
def test_a_moderators_resolved_proposal_is_neither():
    """1459718's proposal is resolved, and written by a moderator"""
    assert _filled(1459718) == (Proposals(), None)


@pytest.mark.usefixtures("db_session")
def test_a_system_comment_without_the_prefix_is_not_auto_proposed():
    assert _filled(8242410) == (Proposals(primary=["cs.CL"]), None)


@pytest.mark.usefixtures("db_session")
def test_the_prefix_written_by_a_moderator_is_not_auto_proposed():
    assert _filled(8242411) == (Proposals(primary=["cs.CL"]), None)


@pytest.mark.usefixtures("db_session")
def test_a_proposal_with_no_log_comment_is_not_auto_proposed():
    assert _filled(8242412) == (Proposals(primary=["cs.CL"]), None)


@pytest.mark.usefixtures("db_session")
def test_the_latest_auto_proposal_wins_and_a_resolved_one_is_not_unresolved():
    """cs.CY was proposed first and resolved, cs.CL later and is still open"""
    assert _filled(8242413) == (Proposals(primary=["cs.CL"]), "cs.CL")


@pytest.mark.usefixtures("db_session")
def test_a_secondary_proposal_is_not_the_auto_proposed_primary():
    assert _filled(8242414) == (Proposals(secondary=["cs.CL"]), None)


@pytest.mark.usefixtures("db_session")
def test_a_submission_with_no_proposals_has_neither():
    assert _filled(201) == (Proposals(), None)
