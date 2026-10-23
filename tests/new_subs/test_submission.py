"""tests for reading the system-proposed primary of a submission from the db"""
import pytest

from app.new_subs.submission import fetch_auto_proposed_primary


@pytest.mark.usefixtures("db_session")
def test_the_system_proposal_is_the_auto_proposed_primary():
    assert fetch_auto_proposed_primary(8242408) == "cs.CL"


@pytest.mark.usefixtures("db_session")
def test_a_moderators_proposal_is_not_auto_proposed():
    """1459718's proposal is resolved, and written by a moderator"""
    assert fetch_auto_proposed_primary(1459718) is None


@pytest.mark.usefixtures("db_session")
def test_a_system_comment_without_the_prefix_is_not_auto_proposed():
    assert fetch_auto_proposed_primary(8242410) is None


@pytest.mark.usefixtures("db_session")
def test_the_prefix_written_by_a_moderator_is_not_auto_proposed():
    assert fetch_auto_proposed_primary(8242411) is None


@pytest.mark.usefixtures("db_session")
def test_a_proposal_with_no_log_comment_is_not_auto_proposed():
    assert fetch_auto_proposed_primary(8242412) is None


@pytest.mark.usefixtures("db_session")
def test_the_latest_auto_proposal_wins():
    assert fetch_auto_proposed_primary(8242413) == "cs.CL"


@pytest.mark.usefixtures("db_session")
def test_a_secondary_proposal_is_not_the_auto_proposed_primary():
    assert fetch_auto_proposed_primary(8242414) is None


@pytest.mark.usefixtures("db_session")
def test_a_submission_with_no_proposals_has_no_auto_proposed_primary():
    assert fetch_auto_proposed_primary(201) is None
