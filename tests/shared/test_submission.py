"""tests for shared submission data fetching"""
import pytest

from app.shared.submission import SubEmailData, get_submission_info


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
    assert result[124].submission_categories == "no primary cs.AI cs.LG"


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_no_categories():
    result = get_submission_info({125})
    assert 125 in result
    assert result[125].submission_categories == "no primary"


@pytest.mark.usefixtures("db_session")
def test_get_submission_info_multiple_ids():
    result = get_submission_info({123, 124, 125})
    assert set(result.keys()) == {123, 124, 125}
    assert result[123].submission_categories == "cs.LG cs.AI"
    assert result[124].submission_categories == "no primary cs.AI cs.LG"
    assert result[125].submission_categories == "no primary"


# ── submission_categories ───────────────────────────────────────────────────

def _sub(primary=None, secondaries=None): #dummy submission creation
    return SubEmailData(
        submission_id=1, title="t", authors="a", status=1,
        submitter_name="n", submitter_id=2,
        primary_category=primary, secondary_categories=secondaries or [],
    )

def test_category_string_primary_and_secondaries():
    assert _sub("cs.LG", ["cs.AI", "math.ST"]).submission_categories == "cs.LG cs.AI math.ST"


def test_category_string_primary_only():
    assert _sub("cs.LG").submission_categories == "cs.LG"


def test_category_string_no_primary():
    assert _sub(None, ["cs.AI", "cs.LG"]).submission_categories == "no primary cs.AI cs.LG"


def test_category_string_nothing_at_all():
    assert _sub().submission_categories == "no primary"


# ── subject_categories ──────────────────────────────────────────────────────
# the subject line keeps the older '-' form

def test_subject_categories_no_primary():
    assert _sub(None, ["cs.AI", "cs.LG"]).subject_categories == "- cs.AI cs.LG"


def test_subject_categories_nothing_at_all():
    assert _sub().subject_categories == "-"


def test_subject_categories_matches_body_when_there_is_a_primary():
    sub = _sub("cs.LG", ["cs.AI"])
    assert sub.subject_categories == sub.submission_categories == "cs.LG cs.AI"
