"""tests for the digest's product rules. pure functions, no database"""
from datetime import datetime
import pytest

from arxiv.submission import statuses

from app.daily_update.submissions import OpenSubmission
from app.shared.submission import SubmissionCat
from app.shared.proposals import Proposals
from app.daily_update.filters import (
    has_test_category,
    is_non_mod_hold,
    is_reported_type,
    is_unheld_replacement,
    get_subs_for_mod,
    report_on,
)


def _cats(primary=None, secondaries=(), unannounced=()) -> list[SubmissionCat]:
    """helper to create a submission category row"""
    def row(category, is_primary):
        return SubmissionCat(
            category=category,
            is_published=category not in unannounced,
            is_primary=is_primary,
        )

    rows = []
    if primary:
        rows.append(row(primary, is_primary=True))
    for cat in secondaries:
        rows.append(row(cat, is_primary=False))
    return rows

def _sub(
    submission_id: int = 1,
    type: str = "new",
    status: int = statuses.SUBMITTED,
    primary: str = "cs.AI",
    secondaries: list[str] = None,
    mod_hold: bool = False,
    new_crosses: set[str] = None,
    proposals: Proposals = None,
) -> OpenSubmission:
    secondaries = secondaries if secondaries is not None else []
    return OpenSubmission(
        submission_id=submission_id,
        title="A Title",
        authors="An Author",
        status=status,
        submitter_name="Sub Mitter",
        submitter_id=1,
        submit_time=datetime(2026, 7, 27, 10, 0),
        sub_type=type,
        categories=_cats(primary, secondaries, new_crosses or set()),
        mod_hold=mod_hold,
        proposals=proposals or Proposals(),
    )


# ── filtering ────────────────────────────────────────────────────────

@pytest.mark.parametrize("good_type", ["new", "rep", "cross"])
def test_reported_types(good_type):
    assert is_reported_type(_sub(type=good_type))


@pytest.mark.parametrize("bad_type", ["wdr", "jref", "bogus", ""])
def test_everything_else_is_not_reported(bad_type):
    assert not is_reported_type(_sub(type=bad_type))


def test_a_replacement_only_counts_while_it_is_held():
    #nothing to moderate on a replacement that is sailing through
    assert is_unheld_replacement(_sub(type="rep", status=statuses.SUBMITTED))
    assert not is_unheld_replacement(_sub(type="rep", status=statuses.ON_HOLD))
    #the rule is about replacements only
    assert not is_unheld_replacement(_sub(type="new", status=statuses.SUBMITTED))
    assert not is_unheld_replacement(_sub(type="cross", status=statuses.SUBMITTED))


def test_remove_non_mod_holds():
    #admin holds and legacy holds both arrive here as mod_hold False
    assert not is_non_mod_hold(_sub(status=statuses.ON_HOLD, mod_hold=True))
    assert is_non_mod_hold(_sub(status=statuses.ON_HOLD, mod_hold=False))
    assert not is_non_mod_hold(_sub(status=statuses.SUBMITTED, mod_hold=False))


def test_test_category_is_excluded():
    assert has_test_category(_sub(primary="test.dis-nn"))
    assert has_test_category(_sub(primary="cs.AI", secondaries=["test.soft"]))
    assert not has_test_category(_sub(primary="cs.AI", secondaries=["cs.LG"]))
    assert not has_test_category(_sub(primary=None, secondaries=["cs.LG"]))

def test_report_on_keeps_only_reportable_submissions():
    subs = [
        _sub(submission_id=1),                                                    #keep
        _sub(submission_id=2, type="rep"),                                        #drop, not held
        _sub(submission_id=3, type="wdr"),                                        #drop
        _sub(submission_id=4, type="jref"),                                        #drop
        _sub(submission_id=5, status=statuses.ON_HOLD, mod_hold=False),          #drop
        _sub(submission_id=6, primary="test.dis-nn"),                             #drop
        _sub(submission_id=8, primary="cs.AI", secondaries=["test.soft"]),        #drop
        _sub(submission_id=7, status=statuses.ON_HOLD, mod_hold=True),           #keep
        _sub(submission_id=10, type="rep", status=statuses.ON_HOLD, mod_hold=True), #keep, held
    ]
    assert [s.submission_id for s in report_on(subs)] == [1, 7, 10]


# ── get_subs_for_mod: whose digest a submission lands in ────────────────────

def test_a_submission_reaches_every_category_it_is_in():
    sub = _sub(type="new", primary="cs.AI", secondaries=["cs.LG"])
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])
    assert sub in get_subs_for_mod({"cs.LG"}, [sub])


def test_a_cross_reaches_only_the_category_it_is_entering():
    #cs.LG is where the paper already lives; cs.AI is the request being made
    sub = _sub(type="cross", primary="cs.LG", secondaries=["cs.AI"], new_crosses={"cs.AI"})
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])
    assert sub not in get_subs_for_mod({"cs.LG"}, [sub])


def test_a_replacement_reaches_every_category_it_is_in():
    sub = _sub(type="rep", primary="cs.LG", secondaries=["cs.AI"])
    assert sub in get_subs_for_mod({"cs.LG"}, [sub])
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])


def test_a_proposed_category_reaches_that_moderator():
    #cs.AI is nowhere on the submission, only proposed for it
    sub = _sub(type="new", primary="astro-ph.HE", proposals=Proposals(secondary=["cs.AI"]))
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])


def test_a_proposed_primary_reaches_that_moderator_too():
    sub = _sub(type="new", primary="astro-ph.HE", proposals=Proposals(primary=["cs.AI"]))
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])


def test_a_proposal_reaches_the_moderator_even_on_a_cross():
    sub = _sub(type="cross", primary="cs.LG", secondaries=["astro-ph.HE"],
               new_crosses={"astro-ph.HE"}, proposals=Proposals(secondary=["cs.AI"]))
    assert sub in get_subs_for_mod({"cs.AI"}, [sub])
    assert sub not in get_subs_for_mod({"cs.LG"}, [sub])


def test_unrelated_categories_get_nothing():
    sub = _sub(type="new", primary="cs.AI")
    assert sub not in get_subs_for_mod({"astro-ph.HE"}, [sub])


def test_the_given_order_is_kept():
    #every one of these matches, so the whole list should come back untouched
    subs = [_sub(submission_id=i, type="new", primary="cs.AI") for i in (5, 3, 9)]
    assert get_subs_for_mod({"cs.AI"}, subs) == subs
