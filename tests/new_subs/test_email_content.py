"""tests for the initial moderator email's layout

Both formats are pinned in full. If the email looks wrong, this is where it shows.
"""
from datetime import datetime, timezone

from app.new_subs.email_content import render_email
from app.new_subs.submission import NewSubmission
from app.new_subs.templates.submission import render_submission
from app.shared.submission import SubmissionCat

CHECK = "https://check.arxiv.org/submit/7853055"
GUIDE = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages"


def _sub(**overrides) -> NewSubmission:
    """a submission with every field the email can show"""
    fields = dict(
        submission_id=7853055,
        title="a great paper about papers",
        authors="Pippin Otter, Nami Cat",
        status=2,
        submitter_name="Nami Cat",
        submitter_id=906580,
        submit_time=datetime(2026, 9, 28, 17, 20, 16, tzinfo=timezone.utc),
        sub_type="new",
        categories=[SubmissionCat(category="gr-qc", is_published=False, is_primary=True),
                    SubmissionCat(category="cs.CG", is_published=False, is_primary=False)],
        comments="i miss summer",
        journal_ref="J. Test. Phys. 42 (2026) 1234",
        doi="10.1000/test.2026.1234",
        abstract="Physics is a cool science",
        system_proposed_primary="physics.hist-ph",
        first_time_submitter=True,
        flagged_submitter=True,
    )
    fields.update(overrides)
    return NewSubmission(**fields)


def _bare(**overrides) -> NewSubmission:
    """the same submission with everything optional left out"""
    return _sub(comments=None, journal_ref=None, doi=None, abstract=None,
                system_proposed_primary=None, first_time_submitter=False,
                flagged_submitter=False, **overrides)


# ── the whole body, every field ─────────────────────────────────────────────

def test_the_whole_text_body():
    assert render_submission(_sub()).text == (
        "** Note: First submission from this submitter **\n"
        "** Warning: This submitter is flagged **\n"
        "\n"
        "submit/7853055 submitted at: 09-28 13:20 EDT by Nami Cat\n"
        f"  Review at: {CHECK}\n"
        "  a great paper about papers\n"
        "  Pippin Otter, Nami Cat\n"
        "\n"
        "  Categories: gr-qc cs.CG\n"
        "  System proposed primary: physics.hist-ph\n"
        "  Status: on hold\n"
        "\n"
        "  Comments: i miss summer\n"
        "  Journal ref: J. Test. Phys. 42 (2026) 1234\n"
        "  DOI: 10.1000/test.2026.1234\n"
        "\n"
        "Abstract:\n"
        "Physics is a cool science\n"
    )


def test_the_whole_html_body():
    assert render_submission(_sub()).html == (
        "<p><b>** Note: First submission from this submitter **</b></p>\n"
        "<p><b>** Warning: This submitter is flagged **</b></p>\n"
        "<p>submit/7853055 submitted at: 09-28 13:20 EDT by Nami Cat<br>\n"
        f'<a href="{CHECK}">Review in arXiv Check</a><br>\n'
        "<b>a great paper about papers</b><br>\n"
        "Pippin Otter, Nami Cat</p>\n"
        "<p><b>Categories:</b> gr-qc cs.CG<br>\n"
        "<b>System proposed primary:</b> physics.hist-ph<br>\n"
        "<b>Status:</b> on hold</p>\n"
        "<p><b>Comments:</b> i miss summer<br>\n"
        "<b>Journal ref:</b> J. Test. Phys. 42 (2026) 1234<br>\n"
        "<b>DOI:</b> 10.1000/test.2026.1234</p>\n"
        "<p><b>Abstract:</b><br>\n"
        "Physics is a cool science</p>\n"
    )


# ── the whole body, nothing optional ────────────────────────────────────────

def test_the_whole_text_body_with_nothing_optional():
    """no warnings, no classifier proposal, no comments block and no abstract"""
    assert render_submission(_bare()).text == (
        "submit/7853055 submitted at: 09-28 13:20 EDT by Nami Cat\n"
        f"  Review at: {CHECK}\n"
        "  a great paper about papers\n"
        "  Pippin Otter, Nami Cat\n"
        "\n"
        "  Categories: gr-qc cs.CG\n"
        "  Status: on hold\n"
    )


def test_the_whole_html_body_with_nothing_optional():
    assert render_submission(_bare()).html == (
        "<p>submit/7853055 submitted at: 09-28 13:20 EDT by Nami Cat<br>\n"
        f'<a href="{CHECK}">Review in arXiv Check</a><br>\n'
        "<b>a great paper about papers</b><br>\n"
        "Pippin Otter, Nami Cat</p>\n"
        "<p><b>Categories:</b> gr-qc cs.CG<br>\n"
        "<b>Status:</b> on hold</p>\n"
    )


# ── the header line ─────────────────────────────────────────────────────────

def test_a_submission_with_no_submit_time_leaves_the_time_out():
    first_line = render_submission(_bare(submit_time=None)).text.split("\n")[0]
    assert first_line == "submit/7853055 by Nami Cat"


def test_a_submission_with_no_submitter_name_falls_back_to_the_id():
    first_line = render_submission(_bare(submitter_name="")).text.split("\n")[0]
    assert first_line == "submit/7853055 submitted at: 09-28 13:20 EDT by user 906580"


# ── missing pieces get a stand-in ───────────────────────────────────────────

def test_a_missing_title_and_authors_say_so():
    text = render_submission(_bare(title="", authors="")).text
    assert "  (no title)\n  (no authors)\n" in text


def test_a_submission_with_no_categories_says_no_primary():
    assert "  Categories: no primary\n" in render_submission(_bare(categories=[])).text


# ── submitter text is escaped ───────────────────────────────────────────────

def test_everything_the_submitter_typed_is_escaped_in_html():
    """title, authors, submitter name and the free-text fields are all user-supplied"""
    html = render_submission(_sub(
        title="a <script> paper", authors="A & B", submitter_name='"quoted"',
        comments="<b>bold</b>", abstract="x > y",
    )).html
    assert "<b>a &lt;script&gt; paper</b>" in html
    assert "A &amp; B" in html
    assert "by &quot;quoted&quot;" in html
    assert "<b>Comments:</b> &lt;b&gt;bold&lt;/b&gt;" in html
    assert "x &gt; y" in html


# ── the authors line ────────────────────────────────────────────────────────

def test_a_long_author_list_is_truncated():
    """MAX_AUTHORS is 7, shared with the digest"""
    authors = ", ".join(f"Author {n}" for n in range(1, 11))
    assert "  Author 1, Author 2, Author 3, Author 4, Author 5, Author 6, Author 7, ...\n" \
        in render_submission(_bare(authors=authors)).text


# ── the email around the body ───────────────────────────────────────────────

def test_the_body_is_followed_by_a_rule_and_the_shared_footer():
    text, html = render_email(_bare())
    assert text == render_submission(_bare()).text + (
        "\n"
        "----------------------------------------\n"
        f"How to use Check: {GUIDE}/1312915466/arXiv+Check+Start+Guide \n"
        f"How to moderate: {GUIDE}/830767115/How+do+I+moderate+a+submission \n"
        f"Moderator Hub: {GUIDE}/812580865/Moderator+Hub \n"
        "\n"
        "This email was generated by the moderator email system version 2.0\n"
        "Some of your arXiv moderation emails may look different. "
        "Throughout 2026, we will be transitioning email systems.\n"
    )
    assert html == render_submission(_bare()).html + (
        "\n<hr>\n"
        f'<p><a href="{GUIDE}/1312915466/arXiv+Check+Start+Guide">How to use Check</a> | '
        f'<a href="{GUIDE}/830767115/How+do+I+moderate+a+submission">How to moderate</a> | '
        f'<a href="{GUIDE}/812580865/Moderator+Hub">Moderator Hub</a></p>\n'
        "<p>This email was generated by the moderator email system version 2.0<br>\n"
        "Some of your arXiv moderation emails may look different. "
        "Throughout 2026, we will be transitioning email systems.</p>\n"
    )
