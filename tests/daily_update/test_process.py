"""end-to-end tests for the digest against the seeded database, with only the send faked"""
from unittest.mock import Mock, patch

import pytest

from app.daily_update.process import send_daily_reports
from app.daily_update.moderators import DigestMod


def _run(mock_send: Mock) -> dict[str, dict]:
    """run the job with sending faked, indexed by the first recipient of each email
    output like "digest-cat@example.com":     {to_emails, subject, text_body, html_body}
    """
    #send_email is mocked out, so the real SEND_EMAILS guard never runs
    with patch("app.daily_update.digest_email.send_email", mock_send):
        send_daily_reports()
    return {call.kwargs["to_emails"][0]: call.kwargs for call in mock_send.call_args_list}


@pytest.fixture 
def sends(db_session): #happy path
    return _run(Mock(return_value=True))


# ── one email per moderator ─────────────────────────────────────────────────

def test_each_moderator_gets_their_own_email(sends):
    #55001 and 55006 both moderate cs.AI, and each is addressed separately
    assert len(sends) == 8
    assert sends["digest-cat@example.com"]["to_emails"] == ["digest-cat@example.com"]
    assert sends["digest-cat2@example.com"]["to_emails"] == ["digest-cat2@example.com"]


def test_every_digest_moderator_gets_an_email(sends):
    assert set(sends.keys()) == {
        "digest-cat@example.com",      #cs.AI
        "digest-cat2@example.com",     #cs.AI as well
        "digest-archive@example.com",  #astro-ph
        "digest-alias@example.com",    #q-fin.EC
        "digest-noemail@example.com",  #nlin.AO, no_email set
        "digest-empty@example.com",    #gr-qc, nothing to report
        "digest-alias2@example.com",   #q-fin.EC, the alias spelling
        "digest-alias-archive@example.com", #the q-fin archive
    }


# ── what lands in a digest ──────────────────────────────────────────────────

def test_category_moderator_gets_their_own_submissions(sends):
    body = sends["digest-cat@example.com"]["body"]
    assert "submit/201" in body #new, cs.AI
    assert "submit/210" in body #a rep on a mod hold, cs.AI
    assert "submit/213" in body #has proposals


def test_a_proposal_for_their_category_is_included(sends):
    #219 is astro-ph.HE; only the unresolved cs.AI proposal puts it in a cs.AI digest
    assert "submit/219" in sends["digest-cat@example.com"]["body"]


def test_other_peoples_categories_are_not_included(sends):
    body = sends["digest-cat@example.com"]["body"]
    assert "submit/205" not in body #astro-ph.HE


@pytest.mark.parametrize("submission_id,why", [
    ("submit/202", "a replacement nobody has held"),
    ("submit/204", "withdrawal"),
    ("submit/209", "admin hold"),
    ("submit/211", "test primary category"),
    ("submit/216", "real primary but a test secondary"),
    ("submit/217", "on a legacy hold"),
    ("submit/212", "journal reference"),
    ("submit/215", "unexpected type"),
    ("submit/207", "already announced, so not an open submission"),
])
def test_excluded_submissions_are_absent(sends, submission_id, why):
    assert submission_id not in sends["digest-cat@example.com"]["body"], why


def test_archive_moderator_gets_the_whole_archive(sends):
    #55002's row names the astro-ph archive, not a category, so every category in it counts
    body = sends["digest-archive@example.com"]["body"]
    assert "submit/205" in body #astro-ph.HE
    assert "submit/220" in body #astro-ph.CO
    assert "submit/201" not in body #cs.AI, a different archive


def test_aliases_connect_in_both_directions(sends):
    #econ.GN and q-fin.EC are the same category under two spellings. either side of the
    #moderator row must reach either side of the stored category
    canonical_mod = sends["digest-alias@example.com"]["body"]   #55003's row says econ.GN
    alias_mod = sends["digest-alias2@example.com"]["body"]      #55007's row says q-fin.EC

    assert "submit/208" in canonical_mod #208 is stored as q-fin.EC
    assert "submit/221" in canonical_mod #221 is stored as econ.GN
    assert "submit/208" in alias_mod
    assert "submit/221" in alias_mod


def test_an_archive_moderator_reaches_across_the_alias(sends):
    #55008 mods the q-fin archive. q-fin.EC lives in it, and econ.GN is the same category
    body = sends["digest-alias-archive@example.com"]["body"]
    assert "submit/208" in body #stored q-fin.EC
    assert "submit/221" in body #stored econ.GN


def test_moderator_with_nothing_still_gets_an_email(sends):
    assert "no new activity" in sends["digest-empty@example.com"]["body"]


# ── the cross rule ──────────────────────────────────────────────────────────

def test_cross_reaches_the_category_it_is_crossing_into(sends):
    #203 lives in cs.LG and is asking for cs.AI
    assert "submit/203" in sends["digest-cat@example.com"]["body"]


def test_cross_does_not_reach_a_category_it_already_lives_in(sends):
    #214 already lives in cs.AI and is asking for cs.LG, so a cs.AI moderator has nothing to do
    assert "submit/214" not in sends["digest-cat@example.com"]["body"]


# ── sections ────────────────────────────────────────────────────────────────

def test_mod_hold_lands_in_the_hold_section(sends):
    body = sends["digest-cat@example.com"]["body"]
    hold_part = body.split("New:")[0]
    assert "submit/210" in hold_part #a rep on hold — the only way a replacement appears at all


def test_new_cross_categories_are_shown(sends):
    body = sends["digest-cat@example.com"]["body"]
    cross_part = body.split("Cross Lists:")[1]
    assert "submit/203" in cross_part


# ── entry content ───────────────────────────────────────────────────────────

def test_proposals_appear_on_the_entry(sends):
    body = sends["digest-cat@example.com"]["body"]
    assert "Primary proposals: cs.CV; Secondary proposals: stat.ML" in body


# ── failure handling ────────────────────────────────────────────────────────

@pytest.mark.usefixtures("db_session")
def test_one_failed_send_does_not_stop_the_rest():
    mock_send = Mock(side_effect=[RuntimeError("smtp down")] + [True] * 7)
    assert len(_run(mock_send)) == 8


@pytest.mark.usefixtures("db_session")
def test_a_moderator_who_missed_out_is_warned_about(caplog):
    mock_send = Mock(side_effect=[RuntimeError("smtp down")] + [True] * 7)
    with patch("app.daily_update.process.settings.SEND_EMAILS", True), caplog.at_level("WARNING"):
        _run(mock_send)
    assert "1 moderators did not get a digest today" in caplog.text


@pytest.mark.usefixtures("db_session")
def test_no_shortfall_warning_when_sending_is_off(caplog):
    #every send reports False by design, which is not a shortfall
    with patch("app.daily_update.process.settings.SEND_EMAILS", False), caplog.at_level("WARNING"):
        _run(Mock(return_value=False))
    assert "did not get a digest" not in caplog.text


@pytest.mark.usefixtures("db_session")
def test_the_job_fails_when_it_reached_nobody():
    #a relay that raises on every send, so no moderator gets a digest. the job has to exit
    #non-zero for Cloud Run to rerun it, and that rerun is safe precisely because nothing
    #was delivered the first time
    relay_down = Mock(side_effect=RuntimeError("smtp down"))
    with patch("app.daily_update.process.settings.SEND_EMAILS", True): #the guards sit out when off
        with pytest.raises(RuntimeError, match="giving up so the job retries"):
            _run(relay_down)


@pytest.mark.usefixtures("db_session")
def test_a_partial_run_exits_cleanly_rather_than_retrying():
    #one got today's digest. failing here would send them a second copy on the retry
    mock_send = Mock(side_effect=[True] + [RuntimeError("smtp down")] * 7)
    with patch("app.daily_update.process.settings.SEND_EMAILS", True):
        assert len(_run(mock_send)) == 8


@pytest.mark.usefixtures("db_session")
def test_nothing_sent_is_not_a_failure_when_sending_is_off():
    #SEND_EMAILS off means every send reports False by design, not because anything broke.
    #so the run has to finish quietly rather than raising the way a real outage would
    with patch("app.daily_update.process.settings.SEND_EMAILS", False):
        attempted = _run(Mock(return_value=False))
    assert len(attempted) == 8 #every moderator was still walked, no exception on the way


@pytest.mark.usefixtures("db_session")
def test_no_warning_when_everyone_got_one(caplog):
    with caplog.at_level("WARNING"):
        _run(Mock(return_value=True))
    assert "did not get a digest" not in caplog.text


@pytest.mark.usefixtures("db_session")
def test_one_failed_render_does_not_stop_the_rest():
    mock_send = Mock(return_value=True)
    mock_render = Mock(side_effect=[ValueError("bad template")] + [("text", "html")] * 7)
    with patch("app.daily_update.digest_email.render_report", mock_render), \
         patch("app.daily_update.digest_email.send_email", mock_send):
        send_daily_reports()
    assert mock_send.call_count == 7


@pytest.mark.usefixtures("db_session")
def test_no_digest_moderators_sends_nothing():
    mock_send = Mock(return_value=True)
    with patch("app.daily_update.process.get_digest_recipients", return_value={}), \
         patch("app.daily_update.digest_email.send_email", mock_send):
        send_daily_reports()
    mock_send.assert_not_called()


@pytest.mark.usefixtures("db_session")
def test_moderator_with_no_user_row_is_skipped():
    mock_send = Mock(return_value=True)
    recipients = {999999: DigestMod(user_id=999999, labels={"cs.AI"}, categories={"cs.AI"})}
    with patch("app.daily_update.process.get_digest_recipients", return_value=recipients), \
         patch("app.daily_update.digest_email.send_email", mock_send):
        send_daily_reports()
    mock_send.assert_not_called()


@pytest.mark.usefixtures("db_session")
def test_no_smtp_connection_when_emails_are_disabled():
    #real send_email here, so the SEND_EMAILS guard is the thing under test
    mock_smtp = Mock()
    with patch("app.shared.utils.email.settings.SEND_EMAILS", False), \
         patch("app.shared.utils.email.smtplib.SMTP_SSL", mock_smtp):
        send_daily_reports()
    mock_smtp.assert_not_called()

# ── the whole digest, end to end ────────────────────────────────────────────
# runs the real job against the seeded db and pins one moderator's html in full. a visual
# check as much as a test: if the digest looks wrong, this is where it shows
# feel free to adjust to match style changes

GUIDE = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages"


def test_the_whole_html_digest_for_one_moderator(sends):
    assert sends["digest-cat@example.com"]["html_body"] == (
        '<p>Daily moderator report for cs.AI</p>\n'
        '<p>If no further actions are taken, all submissions below not currently on hold will be announced at 09-03 20:00 EDT.</p>\n'
        '<p><a href="https://check.arxiv.org/q/todo">Your moderation todo queue</a></p>\n'
        '<h3>On Hold:</h3>\n'
        '<p>07-27 15:00 EDT &nbsp; <b>cs.AI</b> &nbsp; Frank Franky &nbsp; submit/210<br>\n'
        '<a href="https://check.arxiv.org/submit/210">On Mod Hold</a><br>\n'
        'Mod Hold Author<br>\n'
        'Proposals: none</p>\n'
        '<h3>New:</h3>\n'
        '<p>07-27 18:00 EDT &nbsp; <b>cs.AI</b> &nbsp; Frank Franky &nbsp; submit/213<br>\n'
        '<a href="https://check.arxiv.org/submit/213">A Discussed Paper</a><br>\n'
        'Talky Author<br>\n'
        'Primary proposals: cs.CV; Secondary proposals: stat.ML</p>\n'
        '<p>07-27 06:00 EDT &nbsp; <b>cs.AI</b> &nbsp; Frank Franky &nbsp; submit/201<br>\n'
        '<a href="https://check.arxiv.org/submit/201">A New Submission</a><br>\n'
        'New Author<br>\n'
        'Proposals: none</p>\n'
        '<p>07-27 23:00 EDT &nbsp; <b>astro-ph.HE</b> &nbsp; Frank Franky &nbsp; submit/219<br>\n'
        '<a href="https://check.arxiv.org/submit/219">Proposed Into cs.AI</a><br>\n'
        'Proposal Author<br>\n'
        'Secondary proposals: cs.AI</p>\n'
        '<h3>Cross Lists:</h3>\n'
        '<p>07-27 08:00 EDT &nbsp; <b>cs.LG</b> cs.AI &nbsp; Frank Franky &nbsp; submit/203<br>\n'
        '<a href="https://check.arxiv.org/submit/203">A Cross Into cs.AI</a><br>\n'
        'Cross Author<br>\n'
        'Proposals: none</p>\n'
        '<hr>\n'
        f'<p><a href="{GUIDE}/1312915466/arXiv+Check+Start+Guide">How to use Check</a> | <a href="{GUIDE}/830767115/How+do+I+moderate+a+submission">How to moderate</a> | <a href="{GUIDE}/812580865/Moderator+Hub">Moderator Hub</a></p>\n'
        '<p>This email was generated by the moderator email system version 2.0<br>\n'
        'Some of your arXiv moderation emails may look different. Throughout 2026, we will be transitioning email systems.</p>\n'
    )

