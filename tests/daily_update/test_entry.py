"""tests for one submission's entry in the digest. pure rendering, no database"""
from datetime import datetime, timezone

from app.shared.submission import SubmissionCat
from app.shared.proposals import Proposals
from app.daily_update.submissions import OpenSubmission
from app.daily_update.templates.entry import (
    format_categories,
    format_proposals,
    format_timestamp,
    render_entry,
)


def _sub(**overrides) -> OpenSubmission:
    """a whole submission for the render_entry tests. pass categories= to change them"""
    defaults = dict(
        submission_id=201,
        title="A New Submission",
        authors="Nami Cat, Teddy Dog",
        status=1,
        submitter_name="Frank Franky",
        submitter_id=246233,
        submit_time=datetime(2026, 7, 27, 14, 0, tzinfo=timezone.utc),
        sub_type="new",
        categories=[
            SubmissionCat(category="cs.AI", is_published=False, is_primary=True),
            SubmissionCat(category="cs.LG", is_published=False, is_primary=False),
            SubmissionCat(category="hep-lat", is_published=False, is_primary=False),
        ],
    )
    defaults.update(overrides)
    return OpenSubmission(**defaults)


# ── timestamp ───────────────────────────────────────────────────────────────

def test_timestamp_uses_the_shared_format():
    assert format_timestamp(_sub()) == "07-27 10:00 EDT"


def test_missing_submit_time_is_labelled():
    assert format_timestamp(_sub(submit_time=None)) == "(no submit time)"


# ── categories ──────────────────────────────────────────────────────────────

def test_categories_put_primary_first_and_bold_it_in_html():
    text, html_out = format_categories(_sub())
    assert text == "cs.AI cs.LG hep-lat"
    assert html_out == "<b>cs.AI</b> cs.LG hep-lat"


def test_missing_primary_is_labelled():
    only_secondary = [SubmissionCat(category="cs.LG", is_published=True, is_primary=False)]
    text, html_out = format_categories(_sub(categories=only_secondary))
    assert text == "no primary cs.LG"
    assert "<b>no primary</b> cs.LG" in html_out


# ── proposals ───────────────────────────────────────────────────────────────

def test_no_proposals_reads_as_none():
    assert format_proposals(_sub()) == "Proposals: none"


def test_only_secondary_proposals_names_just_that_group():
    sub = _sub(proposals=Proposals(secondary=["stat.ML"]))
    assert format_proposals(sub) == "Secondary proposals: stat.ML"


def test_only_primary_proposals_names_just_that_group():
    sub = _sub(proposals=Proposals(primary=["cs.CV"]))
    assert format_proposals(sub) == "Primary proposals: cs.CV"


def test_both_groups_are_separated():
    sub = _sub(proposals=Proposals(primary=["cs.CV"], secondary=["stat.ML"]))
    assert format_proposals(sub) == "Primary proposals: cs.CV; Secondary proposals: stat.ML"


def test_each_group_is_alphabetical():
    sub = _sub(proposals=Proposals(primary=["math.ST", "cs.CV"],
                                   secondary=["stat.ML", "astro-ph.CO"]))
    assert format_proposals(sub) == (
        "Primary proposals: cs.CV, math.ST; Secondary proposals: astro-ph.CO, stat.ML"
    )


# ── the whole entry ─────────────────────────────────────────────────────────

def test_submitter_falls_back_to_user_id():
    text, _ = render_entry(_sub(submitter_name=""))
    assert "user 246233" in text


def test_entry_text_is_the_whole_product_layout():
    #the indentation is part of it, so this compares the block exactly
    assert render_entry(_sub())[0] == (
        "  07-27 10:00 EDT   cs.AI cs.LG hep-lat   Frank Franky   submit/201\n"
        "    A New Submission\n"
        "    Review at: https://check.arxiv.org/submit/201\n"
        "    Nami Cat, Teddy Dog\n"
        "    Proposals: none\n"
    )


def test_entry_html_is_the_whole_product_layout():
    #&nbsp; keeps the column gaps, which plain spaces would collapse
    assert render_entry(_sub())[1] == (
        '<p>07-27 10:00 EDT &nbsp; <b>cs.AI</b> cs.LG hep-lat &nbsp; Frank Franky &nbsp; submit/201<br>\n'
        '<a href="https://check.arxiv.org/submit/201">A New Submission</a><br>\n'
        'Nami Cat, Teddy Dog<br>\n'
        'Proposals: none</p>\n'
    )


def test_entry_html_links_the_title_to_check():
    _, html_out = render_entry(_sub())
    assert '<a href="https://check.arxiv.org/submit/201">A New Submission</a>' in html_out


def test_entry_escapes_html_in_user_supplied_text():
    sub = _sub(title="Bad <script>", authors="A <b>Name</b>", submitter_name="Ev<il>")
    _, html_out = render_entry(sub)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "<b>Name</b>" not in html_out
    assert "Ev&lt;il&gt;" in html_out


def test_entry_handles_a_submission_with_nothing_filled_in():
    sub = _sub(title="", authors="", submitter_name="", submit_time=None, categories=[])
    text, html_out = render_entry(sub)
    assert "(no title)" in text and "(no authors)" in text and "(no submit time)" in text
    assert "(no title)" in html_out and "(no authors)" in html_out and "(no submit time)" in html_out


def test_entry_truncates_long_author_lists():
    #uses the shared truncate_authors, so just check it is applied
    sub = _sub(authors=", ".join(f"Author {i}" for i in range(30)))
    text, _ = render_entry(sub)
    assert ", ..." in text
