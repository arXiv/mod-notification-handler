"""tests for which new submissions are worth emailing moderators about

Pure rules over an in-memory submission — nothing here needs the database.
"""
import logging

from arxiv.submission import statuses

from app.new_subs.filters import is_notified_type, is_on_auto_hold, notify_about
from app.shared.submission import SubmissionBase, SubmissionCat


def _sub(
    sub_type: str = "new",
    status: int = statuses.SUBMITTED,
    auto_hold: bool = False,
    primary: str = "cs.AI",
    secondaries: list[str] = None,
) -> SubmissionBase:
    rows = [SubmissionCat(category=primary, is_published=False, is_primary=True)] if primary else []
    rows += [
        SubmissionCat(category=cat, is_published=False, is_primary=False)
        for cat in (secondaries or [])
    ]
    return SubmissionBase(
        submission_id=1,
        title="A Title",
        authors="An Author",
        status=status,
        submitter_name="Pippin Otter",
        submitter_id=246234,
        sub_type=sub_type,
        auto_hold=auto_hold,
        categories=rows,
    )


# ── submission type ─────────────────────────────────────────────────────────

def test_new_rep_and_cross_are_notified():
    assert [is_notified_type(_sub(sub_type=t)) for t in ("new", "rep", "cross")] == [True, True, True]


def test_every_other_type_is_dropped():
    """an allow-list, so a withdrawal, a journal ref and an unrecognised type all fail alike"""
    assert [is_notified_type(_sub(sub_type=t)) for t in ("wdr", "jref", "bogus", "")] == [False] * 4


# ── auto hold ───────────────────────────────────────────────────────────────

def test_the_flag_and_the_hold_together_are_an_auto_hold():
    assert is_on_auto_hold(_sub(auto_hold=True, status=statuses.ON_HOLD)) is True


def test_no_flag_is_not_an_auto_hold():
    assert is_on_auto_hold(_sub(auto_hold=False, status=statuses.ON_HOLD)) is False


def test_the_flag_without_the_hold_is_not_an_auto_hold_and_warns(caplog):
    """the two disagreeing is a contradiction, so it is logged rather than assumed either way"""
    with caplog.at_level(logging.WARNING):
        held = is_on_auto_hold(_sub(auto_hold=True, status=statuses.SUBMITTED))
    assert held is False
    assert "auto_hold set but status is 1, not on hold" in caplog.text


def test_no_flag_and_no_hold_logs_nothing(caplog):
    with caplog.at_level(logging.WARNING):
        is_on_auto_hold(_sub(auto_hold=False, status=statuses.SUBMITTED))
    assert caplog.text == ""


# ── everything together ─────────────────────────────────────────────────────

def test_a_plain_new_submission_is_notified_about():
    assert notify_about(_sub()) is True


def test_an_auto_held_submission_is_not():
    assert notify_about(_sub(auto_hold=True, status=statuses.ON_HOLD)) is False


def test_a_withdrawal_is_not():
    assert notify_about(_sub(sub_type="wdr")) is False


def test_a_test_primary_is_not():
    assert notify_about(_sub(primary="test.dis-nn")) is False


def test_a_test_secondary_is_not():
    """a real primary does not rescue a submission with a test category on it"""
    assert notify_about(_sub(primary="cs.AI", secondaries=["test.soft"])) is False
