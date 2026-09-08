"""tests for the message send_email builds

The relay itself is not exercised: SMTP_SSL is replaced, and every assertion is about the
EmailMessage handed to send_message.
"""
from datetime import datetime
from email.utils import parsedate_to_datetime
from unittest.mock import Mock, patch

from app.shared.utils.email import send_email
from app.shared.utils.formatting import ET

SETTINGS = {
    "SEND_EMAILS": True,
    "REDIRECT_EMAILS": False,
    "REDIRECT_RECIPIENT": None,
    "MOD_REPLY_TO": None,
    "ARCHIVAL_EMAIL": None,
    "MAIL_FROM": "magic_email@arxiv.org",
    "HALON_CREDS": "smtps://user:pass@relay.example.com:465",
}


def _send(**overrides):
    """send with the relay faked. returns (result, the message, the kwargs send_message got)"""
    settings = Mock(**{**SETTINGS, **overrides.pop("settings", {})})
    session = Mock()
    session.send_message.return_value = {}
    smtp = Mock()
    smtp.return_value.__enter__ = Mock(return_value=session)
    smtp.return_value.__exit__ = Mock(return_value=False)

    call = {
        "to_emails": ["mod@example.com"],
        "subject": "a subject",
        "body": "text body",
        "html_body": "<p>html body</p>",
    }
    call.update(overrides)

    with patch("app.shared.utils.email.settings", settings), \
         patch("app.shared.utils.email.smtplib.SMTP_SSL", smtp):
        accepted = send_email(**call)

    return accepted, session.send_message.call_args.args[0], session.send_message.call_args.kwargs


# ── headers ─────────────────────────────────────────────────────────────────

def test_the_date_header_is_east_coast_time():
    #the container runs UTC. a naive Date is an hour block wrong for anyone reading it
    _, msg, _ = _send()
    assert parsedate_to_datetime(msg["Date"]).utcoffset() == datetime.now(ET).utcoffset()


def test_from_and_subject_come_from_the_call_and_config():
    _, msg, kwargs = _send()
    assert msg["From"] == "magic_email@arxiv.org"
    assert msg["Subject"] == "a subject"
    assert kwargs["from_addr"] == "magic_email@arxiv.org"


def test_every_message_gets_its_own_id():
    _, first, _ = _send()
    _, second, _ = _send()
    assert first["Message-ID"] and first["Message-ID"] != second["Message-ID"]


# ── threading ───────────────────────────────────────────────────────────────

def test_no_threading_headers_without_a_submission():
    _, msg, _ = _send()
    assert msg["In-Reply-To"] is None
    assert msg["References"] is None


def test_a_submission_threads_every_email_about_it_together():
    _, msg, _ = _send(submission_id=123)
    assert msg["In-Reply-To"] == "<moderation-submit-123@arxiv.org>"
    assert msg["References"] == msg["In-Reply-To"]


# ── the extra addresses ─────────────────────────────────────────────────────

def test_the_mod_reply_to_is_added_to_any_given_ones():
    _, msg, _ = _send(reply_to_emails=["someone@example.com"],
                      settings={"MOD_REPLY_TO": "email2@arxiv.org"})
    assert msg["Reply-To"] == "someone@example.com, email2@arxiv.org"


def test_the_archival_address_is_a_real_bcc():
    #it has to reach the relay without appearing in the headers recipients can see
    _, msg, kwargs = _send(settings={"ARCHIVAL_EMAIL": "email3@arxiv.org"})
    assert "email3@arxiv.org" in kwargs["to_addrs"]
    assert "email3@arxiv.org" not in msg["To"]
    assert msg["Bcc"] is None


# ── both formats ────────────────────────────────────────────────────────────

def test_it_sends_plain_text_with_html_preferred():
    _, msg, _ = _send()
    parts = [p.get_content_type() for p in msg.walk() if p.get_content_maintype() != "multipart"]
    assert parts == ["text/plain", "text/html"] #html last means html preferred


# ── redirecting ─────────────────────────────────────────────────────────────

REDIRECTED = {"REDIRECT_EMAILS": True, "REDIRECT_RECIPIENT": "email1@arxiv.org",
              "MOD_REPLY_TO": "email2@arxiv.org", "ARCHIVAL_EMAIL": "email3@arxiv.org"}


def test_a_redirected_email_reaches_only_the_test_address():
    _, msg, kwargs = _send(settings=REDIRECTED)
    assert kwargs["to_addrs"] == ["email1@arxiv.org"]
    assert msg["To"] == "email1@arxiv.org"
    assert msg["Reply-To"] is None


def test_a_redirected_email_says_who_it_would_have_gone_to():
    _, msg, _ = _send(settings=REDIRECTED)
    text = msg.get_payload(0).get_payload(decode=True).decode()
    assert "[TEST REDIRECT]" in text
    assert "Original To: mod@example.com" in text
    assert "Original Reply-To: email2@arxiv.org" in text
    assert "Original Bcc: email3@arxiv.org" in text


# ── the guard ───────────────────────────────────────────────────────────────

def test_nothing_is_sent_when_sending_is_off():
    smtp = Mock()
    with patch("app.shared.utils.email.settings", Mock(**{**SETTINGS, "SEND_EMAILS": False})), \
         patch("app.shared.utils.email.smtplib.SMTP_SSL", smtp):
        assert send_email(["mod@example.com"], "s", "b", "<p>b</p>") is False
    smtp.assert_not_called()
