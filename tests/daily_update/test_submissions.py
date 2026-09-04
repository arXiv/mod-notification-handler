"""tests for the open-submission query. checks the data, not what any report keeps"""
from unittest.mock import Mock

import pytest

from app.shared.proposals import Proposals, get_unresolved_proposals
from app.daily_update.submissions import get_open_submissions, OpenSubmission
from app.shared.submission import SubmissionCat


@pytest.fixture
def by_id(db_session) -> dict[int, OpenSubmission]:
    return {sub.submission_id: sub for sub in get_open_submissions()}


# ── which rows come back ────────────────────────────────────────────────────

def test_only_open_submissions(by_id: dict[int, OpenSubmission]):
    assert 207 not in by_id #published
    assert 218 not in by_id #working, the submitter hasn't submitted it yet
    assert 201 in by_id #submitted
    assert 210 in by_id #on hold


def test_excluded_types_are_still_returned(by_id: dict[int, OpenSubmission]):
    #the query is not where product rules live, so what filters.py drops still comes back
    assert 204 in by_id #wdr
    assert 212 in by_id #jref


def test_ordered_newest_first(db_session):
    subs = get_open_submissions()
    ids = [sub.submission_id for sub in subs]
    #217 was submitted 2026-07-28 01:00, 201 on 2026-07-27 10:00
    assert ids.index(217) < ids.index(201)
    #whole list ordered
    times = [sub.submit_time for sub in subs if sub.submit_time]
    assert times == sorted(times, reverse=True)


# ── fields ──────────────────────────────────────────────────────────────────

def test_categories_are_split_into_primary_and_secondaries(by_id: dict[int, OpenSubmission]):
    sub = by_id[211]
    assert sub.primary_category == "test.dis-nn"
    assert sub.secondary_categories == ["cs.AI"]
    assert sub.submission_categories == "test.dis-nn cs.AI"


def test_category_rows_keep_both_flags(by_id: dict[int, OpenSubmission]):
    #203: cs.LG primary and announced, cs.AI a secondary that isn't announced yet
    cats = by_id[203].categories
    assert SubmissionCat(category="cs.LG", is_published=True, is_primary=True) in cats
    assert SubmissionCat(category="cs.AI", is_published=False, is_primary=False) in cats


def test_unannounced_categories_are_the_new_crosses(by_id: dict[int, OpenSubmission]):
    #203: cs.LG already announced (is_published=1), cs.AI is the request
    assert by_id[203].new_cross_categories == {"cs.AI"}


def test_announced_category_is_not_a_new_cross(by_id: dict[int, OpenSubmission]):
    #214 is the mirror image of 203: cs.AI is already announced, cs.LG is the request
    assert "cs.AI" not in by_id[214].new_cross_categories


def test_only_a_mod_hold_reason_sets_the_flag(by_id: dict[int, OpenSubmission]):
    assert by_id[210].mod_hold is True   #a mod hold
    assert by_id[209].mod_hold is False  #an admin hold
    assert by_id[217].mod_hold is False  #a legacy hold — on hold with no reason row
    assert by_id[201].mod_hold is False  #not on hold at all, still submitted


# ── proposals ───────────────────────────────────────────────────────────────

def test_unresolved_proposals_are_split_by_primary(by_id: dict[int, OpenSubmission]):
    proposals = by_id[213].proposals
    assert proposals.primary == ["cs.CV"]
    assert proposals.secondary == ["stat.ML"]

def test_resolved_proposals_are_left_out(by_id: dict[int, OpenSubmission]):
    #math.NA on 213 is rejected (status 3)
    proposals = by_id[213].proposals
    assert "math.NA" not in proposals.primary + proposals.secondary

def test_submission_with_no_proposals_gets_an_empty_one(by_id: dict[int, OpenSubmission]):
    #201 has no proposal rows, so it falls back to the default in get_open_submissions
    assert by_id[201].proposals == Proposals()

