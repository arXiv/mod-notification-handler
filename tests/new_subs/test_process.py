"""tests for the db fallbacks process_new_submission fills in before rendering"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from app.new_subs.process import process_new_submission
from app.new_subs.submission import NewSubmission
from app.new_subs.submitter import SubmitterData
from app.shared.proposals import Proposals
from app.shared.submission import SubmissionCat


def _sub(**overrides) -> NewSubmission:
    fields = dict(
        submission_id=8242408,
        title="a great paper about papers",
        authors="Pippin Otter",
        status=4,
        submitter_name="Pippin Otter",
        submitter_id=246234,
        submit_time=datetime(2026, 10, 16, 17, 20, 16, tzinfo=timezone.utc),
        sub_type="new",
        categories=[SubmissionCat(category="cs.CL", is_published=False, is_primary=True)],
        submitter_data=SubmitterData(is_suspect=False, first_time_submitter=False),
    )
    fields.update(overrides)
    return NewSubmission(**fields)


def _process(sub: NewSubmission) -> None:
    with patch("app.new_subs.process.get_recipients", return_value=(["mod@example.com"], [])), \
         patch("app.new_subs.process.send_email", return_value=True):
        process_new_submission(sub)


@pytest.mark.usefixtures("db_session")
def test_the_system_primary_is_read_from_the_db():
    sub = _sub()
    _process(sub)
    assert sub.system_proposed_primary == "cs.CL"



@pytest.mark.usefixtures("db_session")
def test_the_subject_is_the_legacy_subject():
    with patch("app.new_subs.process.get_recipients", return_value=(["mod@example.com"], [])), \
         patch("app.new_subs.process.send_email", return_value=True) as send:
        process_new_submission(_sub())
    assert send.call_args.kwargs["subject"] == "arXiv submission submit/8242408 to cs.CL by Pippin Otter"


@pytest.mark.usefixtures("db_session")
def test_the_unresolved_proposals_are_read_from_the_db():
    sub = _sub()
    _process(sub)
    assert sub.unresolved_proposals == Proposals(primary=["cs.CL"], secondary=[])


@pytest.mark.usefixtures("db_session")
def test_missing_submitter_data_is_read_from_the_db():
    sub = _sub(submitter_data=None)
    _process(sub)
    assert sub.submitter_data == SubmitterData(is_suspect=False, first_time_submitter=True)


@pytest.mark.usefixtures("db_session")
def test_submitter_data_from_the_message_is_kept():
    """246234 is not flagged and is first time in the db, so a different value shows the db was not used"""
    sub = _sub(submitter_data=SubmitterData(is_suspect=True, first_time_submitter=False))
    _process(sub)
    assert sub.submitter_data == SubmitterData(is_suspect=True, first_time_submitter=False)
