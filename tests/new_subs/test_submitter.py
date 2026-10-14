"""tests for reading submitter data from the db"""
import pytest

from app.new_subs.submitter import _fetch_is_suspect


@pytest.mark.usefixtures("db_session")
def test_a_flagged_submitter_is_suspect():
    assert _fetch_is_suspect(246233) is True


@pytest.mark.usefixtures("db_session")
def test_an_unflagged_submitter_is_not_suspect():
    assert _fetch_is_suspect(246234) is False


@pytest.mark.usefixtures("db_session")
def test_a_submitter_with_no_demographics_row_is_not_suspect():
    assert _fetch_is_suspect(246231) is False
