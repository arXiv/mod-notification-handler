"""tests for reading submitter data from the db"""
import pytest

from app.new_subs.submitter import SubmitterData, fetch_submitter_data


@pytest.mark.usefixtures("db_session")
def test_a_flagged_submitter_with_an_announced_paper():
    """246233 has flag_suspect set, and new 207 is announced"""
    assert fetch_submitter_data(246233) == SubmitterData(is_suspect=True, first_time_submitter=False)


@pytest.mark.usefixtures("db_session")
def test_a_submitter_with_only_open_papers_is_first_time():
    """246234's submissions are all still open"""
    assert fetch_submitter_data(246234) == SubmitterData(is_suspect=False, first_time_submitter=True)


@pytest.mark.usefixtures("db_session")
def test_a_submitter_with_no_demographics_row_is_not_flagged():
    assert fetch_submitter_data(246231) == SubmitterData(is_suspect=False, first_time_submitter=True)
