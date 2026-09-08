"""tests for assembling a whole digest: report_body layout and report_content composition"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from arxiv.submission import statuses

from app.shared.proposals import Proposals
from app.shared.templates import Rendered
from app.shared.submission import SubmissionCat
from app.daily_update.submissions import OpenSubmission
from app.daily_update.report_content import (
    MatchRank, bucket, match_rank,
    render_entries, render_report, section_for,
)
from app.daily_update.moderators import DigestMod
from app.daily_update.templates.report_body import (
    EMPTY_SECTION, MOD_TODO_TITLE, MOD_TODO_URL,NOTHING_TO_REPORT, Section,
    announce_line, render_body, render_header, render_section,
)

#helpers

def _cat(name: str, primary: bool = False, published: bool = False) -> SubmissionCat:
    """one assigned category row"""
    return SubmissionCat(category=name, is_published=published, is_primary=primary)


def _sub(submission_id: int = 1, type: str = "new", status: int = 1,
         categories: list[SubmissionCat] = None,
         mod_hold: bool = False) -> OpenSubmission:
    return OpenSubmission(
        submission_id=submission_id,
        title="A Fabulous Foray into Wildlife",
        authors="Nami Cat",
        status=status,
        submitter_name="Nami Cat",
        submitter_id=246233,
        submit_time=datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc),
        sub_type=type,
        categories=[_cat("cs.AI", primary=True)] if categories is None else categories,
        mod_hold=mod_hold,
    )


def _mod(labels=("cs.AI",), categories=("cs.AI",)) -> DigestMod:
    return DigestMod(user_id=1, labels=set(labels), categories=set(categories))


# ── the section list itself ─────────────────────────────────────────────────
# literals, so a reorder, a retitle or a dropped section fails here

def test_sections_are_in_this_order_with_these_headings():
    assert [section.value for section in Section] == ["On Hold", "New", "Cross Lists"]


# ── header ──────────────────────────────────────────────────────────────────

def test_header_text_is_the_whole_layout():
    assert render_header("cs.AI").text == (
        "Daily moderator report for cs.AI\n"
        "\n"
        f"{announce_line()}\n"
        "\n"
        "Your moderation todo queue: https://check.arxiv.org/q/todo\n"
    )


def test_header_html_is_the_whole_layout():
    assert render_header("cs.AI").html == (
        "<p>Daily moderator report for cs.AI</p>\n"
        f"<p>{announce_line()}</p>\n"
        '<p><a href="https://check.arxiv.org/q/todo">Your moderation todo queue</a></p>\n'
    )


def test_the_announce_line_uses_the_time_in_east_coast_terms():
    #20:00 EDT on the 30th is already the 31st in UTC, and moderators read ET
    at = datetime(2026, 7, 31, 0, 0, tzinfo=timezone.utc)
    with patch("app.daily_update.announce.next_announce_time", return_value=at):
        assert announce_line() == (
            "If no further actions are taken, all submissions below not currently on hold "
            "will be announced at 07-30 20:00 EDT."
        )


def test_the_announce_line_still_renders_when_arxiv_did_not_answer():
    with patch("app.daily_update.announce.next_announce_time", return_value=None):
        assert announce_line() == (
            "If no further actions are taken, all submissions below not currently on hold "
            "will be announced at (time unavailable)."
        )


def test_header_sorts_labels():
    assert _mod(labels=("cs.LG", "cs.AI")).header == "cs.AI cs.LG"


# ── sections ────────────────────────────────────────────────────────────────

def test_section_uses_its_title_not_its_key():
    text, html_out = render_section(Section.HOLD, [Rendered("entry\n", "<p>entry</p>\n")])
    assert Section.HOLD.value in text
    assert Section.HOLD.value in html_out


def test_empty_section_says_none():
    text, html_out = render_section(Section.NEW, [])
    assert EMPTY_SECTION in text
    assert EMPTY_SECTION in html_out


# ── whole body ──────────────────────────────────────────────────────────────

def test_empty_report_is_still_a_report():
    text, html_out = render_body("cs.AI", {section: [] for section in Section})
    assert NOTHING_TO_REPORT in text
    assert NOTHING_TO_REPORT in html_out
    #no section headings when there is nothing at all
    assert Section.NEW.value not in text


def test_a_section_with_content_still_shows_none_under_the_empty_ones():
    entries = {section: [] for section in Section}
    entries[Section.NEW] = [Rendered("a new one\n", "<p>a new one</p>\n")]
    report = render_body("cs.AI", entries)

    body_text = report.text.split(f"{MOD_TODO_URL}\n")[1].split("How to use Check")[0]
    assert body_text == (
        "\n"
        "On Hold:\n"
        f"  none\n"
        "\n"
        "New:\n"
        "a new one\n"
        "\n"
        "Cross Lists:\n"
        f"  none\n"
        "\n"
    )

    body_html = report.html.split(f"{MOD_TODO_TITLE}</a></p>\n")[1].split("<hr>")[0]
    assert body_html == (
        "<h3>On Hold:</h3>\n"
        f"<p>none</p>\n"
        "<h3>New:</h3>\n"
        "<p>a new one</p>\n"
        "<h3>Cross Lists:</h3>\n"
        f"<p>none</p>\n"
    )


def test_sections_appear_in_this_order():
    entries = {section: [Rendered(f"{section.value} entry\n", "\n")] for section in Section}
    text, _ = render_body("cs.AI", entries)
    positions = [text.index(t) for t in ("On Hold:", "New:", "Cross Lists:")]
    assert positions == sorted(positions)


def test_report_always_ends_with_the_shared_footer():
    text, html_out = render_body("cs.AI", {section: [] for section in Section})
    assert "moderator email system version 2.0" in text
    assert "Moderator Hub" in html_out


# ── composition ─────────────────────────────────────────────────────────────

def test_each_submission_becomes_one_entry_under_its_own_section():
    buckets = {section: [] for section in Section}
    buckets[Section.NEW] = [_sub(201), _sub(202)]

    rendered = render_entries(buckets)

    assert set(rendered) == set(Section)         #grouping is kept, empty sections included
    assert len(rendered[Section.NEW]) == 2       #one rendered pair per submission
    assert rendered[Section.HOLD] == []
    assert rendered[Section.CROSS] == []


def test_render_report_places_submissions_in_the_right_section():
    subs = [_sub(201, "new"), _sub(210, "rep", status=2), _sub(203, "cross")]
    text, _ = render_report(_mod(), subs)

    hold_part = text.split(f"{Section.NEW.value}:")[0]
    assert "submit/210" in hold_part #on hold beats its rep type

    new_part = text.split(f"{Section.NEW.value}:")[1].split(
        f"{Section.CROSS.value}:")[0]
    assert "submit/201" in new_part

    cross_part = text.split(f"{Section.CROSS.value}:")[1]
    assert "submit/203" in cross_part


def test_a_report_covering_two_categories_holds_both_and_orders_them():
    mod = _mod(labels=("cs.AI", "cs.LG"), categories=("cs.AI", "cs.LG"))
    subs = [
        _build_sub_with_cats(301, primary="cs.CV", secondaries=["cs.AI"]),
        _build_sub_with_cats(302, primary="cs.LG"),
    ]
    text, _ = render_report(mod, subs)

    assert "Daily moderator report for cs.AI cs.LG" in text
    #302 matches on its primary, 301 only on a secondary, so 302 comes first
    new_part = text.split(f"{Section.NEW.value}:")[1]
    assert new_part.index("submit/302") < new_part.index("submit/301")


def test_render_report_with_no_submissions_is_the_empty_report():
    text, _ = render_report(_mod(), [])
    assert NOTHING_TO_REPORT in text


# ── sections ────────────────────────────────────────────────────────────────

def test_section_type_sort():
    assert section_for(_sub(type="new")) == Section.NEW
    assert section_for(_sub(type="cross")) == Section.CROSS
    assert section_for(_sub(type="rep", status=statuses.ON_HOLD, mod_hold=True)) == Section.HOLD
    assert section_for(_sub(type="new", status=statuses.ON_HOLD, mod_hold=True)) == Section.HOLD


def test_bucket_groups_by_section_and_keeps_order():
    subs = [
        _sub(submission_id=1, type="new"),
        _sub(submission_id=2, type="new"),
        _sub(submission_id=3, type="rep", status=statuses.ON_HOLD, mod_hold=True),
    ]
    buckets = bucket(subs, {"cs.AI"})
    assert [s.submission_id for s in buckets[Section.NEW]] == [1, 2]
    assert [s.submission_id for s in buckets[Section.HOLD]] == [3]
    assert buckets[Section.CROSS] == []


# ── ordering within a section ───────────────────────────────────────────────

def _build_sub_with_cats(submission_id, primary=None, secondaries=None, proposed=None, type="new"):
    cats = [_cat(primary, primary=True)] + [_cat(c) for c in (secondaries or [])]
    sub = _sub(submission_id=submission_id, type=type, categories=cats)
    sub.proposals = Proposals(secondary=list(proposed or []))
    return sub


def test_rank_primary_beats_proposed_beats_secondary():
    cats = {"cs.AI"}
    assert match_rank(_build_sub_with_cats(1, primary="cs.AI"), cats) == MatchRank.PRIMARY
    assert match_rank(_build_sub_with_cats(2, primary="cs.LG", proposed=["cs.AI"]), cats) == MatchRank.PROPOSED
    assert match_rank(_build_sub_with_cats(3, primary="cs.LG", secondaries=["cs.AI"]), cats) == MatchRank.SECONDARY
    assert MatchRank.PRIMARY < MatchRank.PROPOSED < MatchRank.SECONDARY


def test_a_submission_that_matches_nothing_is_an_error():
    #bucket only ever sees what get_subs_for_mod picked, so no match means the caller is wrong
    sub = _build_sub_with_cats(1, primary="cs.LG", secondaries=["cs.CV"])
    with pytest.raises(ValueError, match="nothing matches"):
        match_rank(sub, {"astro-ph.HE"})


def test_primary_wins_even_when_also_proposed():
    sub = _build_sub_with_cats(1, primary="cs.AI", proposed=["cs.AI"])
    assert match_rank(sub, {"cs.AI"}) == MatchRank.PRIMARY


def test_proposed_wins_over_secondary():
    sub = _build_sub_with_cats(1, primary="cs.CV", secondaries=["cs.AI"], proposed=["cs.AI"])
    assert match_rank(sub, {"cs.AI"}) == MatchRank.PROPOSED


def test_covering_several_categories_ranks_by_the_best_of_them():
    #they moderate both. cs.AI is only a secondary, but cs.LG is the primary
    sub = _build_sub_with_cats(1, primary="cs.LG", secondaries=["cs.AI"])
    assert match_rank(sub, {"cs.AI"}) == MatchRank.SECONDARY
    assert match_rank(sub, {"cs.AI", "cs.LG"}) == MatchRank.PRIMARY


def test_a_section_is_ranked_across_every_category_covered():
    subs = [
        _build_sub_with_cats(1, primary="cs.CV", secondaries=["cs.AI"]),
        _build_sub_with_cats(2, primary="cs.CV", proposed=["cs.LG"]),
        _build_sub_with_cats(3, primary="cs.LG"),
    ]
    buckets = bucket(subs, {"cs.AI", "cs.LG"})
    #3 primary, 2 proposed, 1 secondary — each matching on a different one of their categories
    assert [s.submission_id for s in buckets[Section.NEW]] == [3, 2, 1]


def test_new_section_orders_primary_then_proposed_then_secondary():
    subs = [
        _build_sub_with_cats(1, primary="cs.LG", secondaries=["cs.AI"]),
        _build_sub_with_cats(2, primary="cs.LG", proposed=["cs.AI"]),
        _build_sub_with_cats(3, primary="cs.AI"),
    ]
    buckets = bucket(subs, {"cs.AI"})
    assert [s.submission_id for s in buckets[Section.NEW]] == [3, 2, 1]


def test_hold_section_ordering():
    subs = [
        _build_sub_with_cats(1, primary="cs.LG", secondaries=["cs.AI"], type="rep"),
        _build_sub_with_cats(2, primary="cs.AI", type="rep"),
    ]
    for s in subs:
        s.status = statuses.ON_HOLD
        s.mod_hold = True
    buckets = bucket(subs, {"cs.AI"})
    assert [s.submission_id for s in buckets[Section.HOLD]] == [2, 1]


def test_crosses_ordering():
    #2 is crossing into their primary, 1 only into a secondary, 3 is merely proposed
    subs = [
        _build_sub_with_cats(1, primary="cs.LG", secondaries=["cs.AI"], type="cross"),
        _build_sub_with_cats(2, primary="cs.AI", type="cross"),
        _build_sub_with_cats(3, primary="cs.LG", proposed=["cs.AI"], type="cross"),
    ]
    buckets = bucket(subs, {"cs.AI"})
    assert [s.submission_id for s in buckets[Section.CROSS]] == [2, 3, 1]


def test_equal_rank_keeps_submit_order():
    #submissions arrive newest first and the sort is stable
    subs = [_build_sub_with_cats(1, primary="cs.AI"), _build_sub_with_cats(2, primary="cs.AI"), _build_sub_with_cats(3, primary="cs.AI")]
    buckets = bucket(subs, {"cs.AI"})
    assert [s.submission_id for s in buckets[Section.NEW]] == [1, 2, 3]
