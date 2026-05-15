"""unit tests for email_content render functions"""
from datetime import datetime, timezone

import pytest

from app.schema import SimplifiedNotification, CommentData, PromoteData, NewPropData, PropRespData
from app.schema import SubEmailData
from app.email_content import get_submission_info, _build_category_string, render_change_block
from app.templates.comment import render_comment_block
from app.templates.promote import render_promote_block
from app.templates.new_prop import render_new_prop_block
from app.templates.prop_resp import render_prop_resp_block
from app.templates.submission import render_submission_block
from app.templates.email_body import render_email, CHECK_GUIDE_URL, HOW_TO_MOD_URL, MOD_HUB_URL

_TIME = datetime(2024, 6, 15, 14, 30, tzinfo=timezone.utc)
_USER = "Alice Mod"


def _note(data) -> SimplifiedNotification:
    return SimplifiedNotification(time=_TIME, user_id=1, data=data)


# ── comment ───────────────────────────────────────────────────────────────────

def test_render_comment_block():
    note = _note(CommentData(comment="looks good to me"))
    text, html_out = render_comment_block(note, _USER)
    assert "looks good to me" in text and "looks good to me" in html_out
    assert _USER in text and _USER in html_out
    assert "ET" in text

def test_render_comment_escapes_html():
    note = _note(CommentData(comment="<script>alert('xss')</script> & done"))
    _, html_out = render_comment_block(note, _USER)
    assert "<script>" not in html_out
    assert "&lt;script&gt;" in html_out
    assert "&amp;" in html_out


# ── promote ───────────────────────────────────────────────────────────────────

def test_render_promote_block():
    note = _note(PromoteData(category="hep-lat", promotion_type="primary", category_change="Promoted category hep-lat to primary; cs.LG cs.AI cs.DC hep-ph => hep-lat cs.AI cs.DC cs.LG hep-ph"))
    text, html_out = render_promote_block(note, _USER)
    assert "primary" in text and "primary" in html_out
    assert "hep-lat" in text and "hep-lat" in html_out
    assert "Promoted category hep-lat to primary" in text and "Promoted category hep-lat to primary" in html_out
    assert _USER in text and _USER in html_out


# ── new proposal ──────────────────────────────────────────────────────────────

def test_render_new_prop_block():
    note = _note(NewPropData(msg="New category(ies) proposed. primary: q-bio.NC"))
    text, html_out = render_new_prop_block(note, _USER)
    assert "New category(ies) proposed. primary: q-bio.NC" in text and "New category(ies) proposed. primary: q-bio.NC" in html_out
    assert _USER in text and _USER in html_out


# ── proposal response ─────────────────────────────────────────────────────────

def test_render_prop_resp_block():
    note = _note(PropRespData(responses="Primary accepted: hep-lat", category_change="no primary -> hep-lat"))
    text, html_out = render_prop_resp_block(note, _USER)
    assert "Primary accepted: hep-lat" in text and "Primary accepted: hep-lat" in html_out
    assert "no primary -> hep-lat" in text and "no primary -> hep-lat" in html_out
    assert _USER in text and _USER in html_out


# ── dispatcher ────────────────────────────────────────────────────────────────

def test_render_change_block_dispatches():
    comment = _note(CommentData(comment="hi"))
    text, html_out = render_change_block(comment, _USER)
    assert "hi" in text and "hi" in html_out
    assert _USER in text and _USER in html_out

    promote = _note(PromoteData(category="cs.AI", promotion_type="secondary", category_change="Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI"))
    text, html_out = render_change_block(promote, _USER)
    assert "secondary" in text and "secondary" in html_out
    assert "Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI" in text and "Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI" in html_out

    new_prop = _note(NewPropData(msg="New category(ies) proposed. primary: cs.AI math.NA"))
    text, html_out = render_change_block(new_prop, _USER)
    assert "cs.AI math.NA" in text and "cs.AI math.NA" in html_out

    prop_resp = _note(PropRespData(
        responses="Proposal Responses: Primary accepted: eess.AS; Secondary accepted: q-bio.BM; Primary rejected: q-bio.BM",
        category_change="cs.LG cs.DC hep-ph => eess.AS cs.DC cs.LG hep-ph q-bio.BM",
    ))
    text, html_out = render_change_block(prop_resp, _USER)
    assert "eess.AS" in text and "eess.AS" in html_out
    assert "q-bio.BM" in text and "q-bio.BM" in html_out
    assert "cs.LG cs.DC hep-ph => eess.AS cs.DC cs.LG hep-ph q-bio.BM" in text and "cs.LG cs.DC hep-ph => eess.AS cs.DC cs.LG hep-ph q-bio.BM" in html_out


# ── submission block ──────────────────────────────────────────────────────────

def _mock_submission(submission_id=123, title="ML Paper", authors="Alice, Bob", status=1,
                     submission_categories="cs.LG cs.AI"):
    return SubEmailData(
        submission_id=submission_id,
        title=title,
        authors=authors,
        status=status,
        submitter_name="",
        submitter_id=0,
        submission_categories=submission_categories,
    )

def test_render_submission_block():
    sub = _mock_submission()
    text, html_out = render_submission_block(sub)
    assert "ML Paper" in text and "ML Paper" in html_out
    assert "Alice, Bob" in text and "Alice, Bob" in html_out
    assert "submitted" in text and "submitted" in html_out
    assert "cs.LG cs.AI" in text and "cs.LG cs.AI" in html_out

def test_render_submission_block_escapes_html():
    sub = _mock_submission(title="<b>Bold</b> Title & More", authors="Author & <Co>")
    _, html_out = render_submission_block(sub)
    assert "<b>Bold</b>" not in html_out
    assert "&lt;b&gt;" in html_out
    assert "&amp;" in html_out


# ── full email ────────────────────────────────────────────────────────────────

def test_render_email_contains_all_sections_and_footer():
    sub = _mock_submission()

    sub_text, sub_html = render_submission_block(sub)

    changes = [
        _note(CommentData(comment="first comment")),
        _note(PromoteData(category="cs.AI", promotion_type="secondary", category_change="Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI")),
        _note(PropRespData(responses="Primary accepted: hep-lat", category_change="no primary -> hep-lat")),
    ]
    change_texts, change_htmls = [], []
    for c in changes:
        ct, ch = render_change_block(c, _USER)
        change_texts.append(ct)
        change_htmls.append(ch)

    body_text, body_html = render_email(sub_text, sub_html, change_texts, change_htmls)

    # submission info present
    assert "ML Paper" in body_text and "ML Paper" in body_html

    # all three change types present
    assert "first comment" in body_text and "first comment" in body_html
    assert "Promoted category cs.AI to secondary" in body_text and "Promoted category cs.AI to secondary" in body_html
    assert "Primary accepted: hep-lat" in body_text and "Primary accepted: hep-lat" in body_html
    assert "no primary -> hep-lat" in body_text and "no primary -> hep-lat" in body_html

    # footer links present in both
    for url in [CHECK_GUIDE_URL, HOW_TO_MOD_URL, MOD_HUB_URL]:
        assert url in body_text, f"missing {url} in text"
        assert url in body_html, f"missing {url} in html"


# ── exact output tests ────────────────────────────────────────────────────────
#will need to be updated whenever format changes
#feel free to delete if too annoying, but its kind of nice to see the whole output
_WHEN = "06-15 10:30 ET"  # _TIME (2024-06-15 14:30 UTC) converted to EDT
_CHECK_URL_123 = "https://check.arxiv.org/submit/123"


def test_comment_exact_text():
    note = _note(CommentData(comment="looks good"))
    text, _ = render_comment_block(note, _USER)
    assert text == f"[{_WHEN}] {_USER} added a comment:\n  looks good\n"


def test_comment_exact_html():
    note = _note(CommentData(comment="looks good"))
    _, html_out = render_comment_block(note, _USER)
    assert html_out == (
        f"<p><strong>[{_WHEN}] {_USER}</strong> added a comment:<br>\n"
        f"looks good</p>\n"
    )


def test_promote_exact_text():
    note = _note(PromoteData(category="hep-lat", promotion_type="primary", category_change="Promoted category hep-lat to primary; cs.LG cs.AI cs.DC hep-ph => hep-lat cs.AI cs.DC cs.LG hep-ph"))
    text, _ = render_promote_block(note, _USER)
    assert text == (
        f"[{_WHEN}] {_USER} promoted hep-lat to primary:\n"
        f"  Change: Promoted category hep-lat to primary; cs.LG cs.AI cs.DC hep-ph => hep-lat cs.AI cs.DC cs.LG hep-ph\n"
    )


def test_promote_exact_html():
    note = _note(PromoteData(category="hep-lat", promotion_type="primary", category_change="Promoted category hep-lat to primary; cs.LG cs.AI cs.DC hep-ph => hep-lat cs.AI cs.DC cs.LG hep-ph"))
    _, html_out = render_promote_block(note, _USER)
    assert html_out == (
        f"<p><strong>[{_WHEN}] {_USER}</strong> promoted hep-lat to primary<br>\n"
        f"Change: Promoted category hep-lat to primary; cs.LG cs.AI cs.DC hep-ph => hep-lat cs.AI cs.DC cs.LG hep-ph</p>\n"
    )


def test_new_prop_exact_text():
    note = _note(NewPropData(msg="New category(ies) proposed. primary: q-bio.NC"))
    text, _ = render_new_prop_block(note, _USER)
    assert text == f"[{_WHEN}] {_USER} submitted a new category proposal:\n  New category(ies) proposed. primary: q-bio.NC\n"


def test_new_prop_exact_html():
    note = _note(NewPropData(msg="New category(ies) proposed. primary: q-bio.NC"))
    _, html_out = render_new_prop_block(note, _USER)
    assert html_out == (
        f"<p><strong>[{_WHEN}] {_USER}</strong> submitted a new category proposal:<br>\n"
        f"New category(ies) proposed. primary: q-bio.NC</p>\n"
    )


def test_prop_resp_exact_text():
    note = _note(PropRespData(responses="Primary accepted: hep-lat", category_change="no primary -> hep-lat"))
    text, _ = render_prop_resp_block(note, _USER)
    assert text == (
        f"[{_WHEN}] {_USER} responded to category proposal(s):\n"
        f"  Primary accepted: hep-lat\n"
        f"  Change: no primary -> hep-lat\n"
    )


def test_prop_resp_exact_html():
    note = _note(PropRespData(responses="Primary accepted: hep-lat", category_change="no primary -> hep-lat"))
    _, html_out = render_prop_resp_block(note, _USER)
    assert html_out == (
        f"<p><strong>[{_WHEN}] {_USER}</strong> responded to category proposal(s):<br>\n"
        f"Primary accepted: hep-lat<br>\n"
        f"Change: no primary -> hep-lat</p>\n"
    )


def test_submission_exact_text():
    sub = _mock_submission()
    text, _ = render_submission_block(sub)
    assert text == (
        "Submission: submit/123\n"
        "Title:      ML Paper\n"
        "Authors:    Alice, Bob\n"
        "Status:     submitted\n"
        "Current Categories: cs.LG cs.AI\n"
        f"View in Check: {_CHECK_URL_123}\n"
    )


def test_submission_exact_html():
    sub = _mock_submission()
    _, html_out = render_submission_block(sub)
    assert html_out == (
        "<p><strong>Submission:</strong> submit/123<br>\n"
        "<strong>Title:</strong> ML Paper<br>\n"
        "<strong>Authors:</strong> Alice, Bob<br>\n"
        "<strong>Status:</strong> submitted<br>\n"
        "<strong>Current Categories:</strong> cs.LG cs.AI<br>\n"
        f"<strong>View in Check:</strong> <a href=\"{_CHECK_URL_123}\">{_CHECK_URL_123}</a></p>\n"
    )


_CHECK_URL = "https://check.arxiv.org/submit/123"
_GUIDE_URL = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/1312915466/arXiv+Check+Start+Guide"
_MOD_URL   = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/830767115/How+do+I+moderate+a+submission"
_HUB_URL   = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/812580865/Moderator+Hub"

def test_full_email_exact_text():
    sub = _mock_submission()
    comment = _note(CommentData(comment="looks good"))
    promote = _note(PromoteData(category="cs.AI", promotion_type="secondary", category_change="Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI"))
    sub_text, sub_html = render_submission_block(sub)
    comment_text, comment_html = render_change_block(comment, _USER)
    promote_text, promote_html = render_change_block(promote, _USER)
    body_text, _ = render_email(sub_text, sub_html, [comment_text, promote_text], [comment_html, promote_html])
    assert body_text == (
        "Submission: submit/123\n"
        "Title:      ML Paper\n"
        "Authors:    Alice, Bob\n"
        "Status:     submitted\n"
        "Current Categories: cs.LG cs.AI\n"
        f"View in Check: {_CHECK_URL}\n"
        "\n"
        "----------------------------------------\n"
        f"[{_WHEN}] {_USER} added a comment:\n"
        "  looks good\n"
        "----------------------------------------\n"
        f"[{_WHEN}] {_USER} promoted cs.AI to secondary:\n"
        "  Change: Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI\n"
        "\n"
        "----------------------------------------\n"
        f"How to use Check: {_GUIDE_URL} \n"
        f"How to moderate: {_MOD_URL} \n"
        f"Moderator Hub: {_HUB_URL} \n"
    )


def test_full_email_exact_html():
    sub = _mock_submission()
    comment = _note(CommentData(comment="looks good"))
    promote = _note(PromoteData(category="cs.AI", promotion_type="secondary", category_change="Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI"))
    sub_text, sub_html = render_submission_block(sub)
    comment_text, comment_html = render_change_block(comment, _USER)
    promote_text, promote_html = render_change_block(promote, _USER)
    _, body_html = render_email(sub_text, sub_html, [comment_text, promote_text], [comment_html, promote_html])
    assert body_html == (
        "<p><strong>Submission:</strong> submit/123<br>\n"
        "<strong>Title:</strong> ML Paper<br>\n"
        "<strong>Authors:</strong> Alice, Bob<br>\n"
        "<strong>Status:</strong> submitted<br>\n"
        "<strong>Current Categories:</strong> cs.LG cs.AI<br>\n"
        f"<strong>View in Check:</strong> <a href=\"{_CHECK_URL}\">{_CHECK_URL}</a></p>\n"
        "\n"
        "<hr>\n"
        f"<p><strong>[{_WHEN}] {_USER}</strong> added a comment:<br>\n"
        "looks good</p>\n"
        f"<p><strong>[{_WHEN}] {_USER}</strong> promoted cs.AI to secondary<br>\n"
        "Change: Promoted category cs.AI to secondary; hep-lat => hep-lat cs.AI</p>\n"
        "\n"
        "<hr>\n"
        f"<p><a href=\"{_GUIDE_URL}\">How to use Check</a> | "
        f"<a href=\"{_MOD_URL}\">How to moderate</a> | "
        f"<a href=\"{_HUB_URL}\">Moderator Hub</a></p>\n"
    )


# ── _build_category_string unit tests ─────────────────────────────────────────

def test_category_string_empty():
    assert _build_category_string([]) == "no primary"


def test_category_string_primary_only():
    assert _build_category_string([("cs.LG", 1)]) == "cs.LG"


def test_category_string_primary_and_cross():
    # math.ST is canonical target of stat.TH alias → stat.TH also added
    result = _build_category_string([("cs.LG", 1), ("cs.AI", 0), ("math.ST", 0)])
    assert result == "cs.LG cs.AI math.ST stat.TH"


def test_category_string_no_primary_with_secondaries():
    result = _build_category_string([("cs.AI", 0), ("cs.LG", 0)])
    assert result == "no primary cs.AI cs.LG"


def test_category_string_alias_expansion():
    # math-ph is canonical target of math.MP alias → math.MP added to secondaries
    result = _build_category_string([("cs.LG", 0), ("math-ph", 1)])
    assert result == "math-ph cs.LG math.MP"


# ── get_submission_info DB tests ──────────────────────────────────────────────

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


