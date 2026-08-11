"""tests for shared submission data fetching"""
import pytest

from app.shared.submission import get_submission_info


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_primary_and_cross():
    result = get_submission_info({123})
    assert 123 in result
    sub = result[123]
    assert sub.title == "A Test Paper on Machine Learning"
    assert sub.authors == "Author One, Author Two"
    assert sub.submission_categories == "cs.LG cs.AI"


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_no_primary_has_secondaries():
    result = get_submission_info({124})
    assert 124 in result
    assert result[124].submission_categories == "- cs.AI cs.LG"


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_no_categories():
    result = get_submission_info({125})
    assert 125 in result
    assert result[125].submission_categories == "-"


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_multiple_ids():
    result = get_submission_info({123, 124, 125})
    assert set(result.keys()) == {123, 124, 125}
    assert result[123].submission_categories == "cs.LG cs.AI"
    assert result[124].submission_categories == "- cs.AI cs.LG"
    assert result[125].submission_categories == "-"
