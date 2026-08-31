"""tests for assembling and sending one moderator's digest email"""
import smtplib
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest

from app.daily_update.digest_email import SEND_ATTEMPTS, _send_with_retry
from app.shared.utils.formatting import ET
from app.daily_update.digest_email import send_digest
from app.daily_update.schema import DigestMod

MOD = DigestMod(user_id=1, labels={"cs.AI"}, categories={"cs.AI"})


def _send(relay: Mock) -> tuple[bool, Mock]:
    """call send_digest with the relay faked. returns (what send_digest returned, the relay)"""
    with patch("app.daily_update.digest_email.send_email", relay):
        accepted = send_digest(MOD, [], "mod@example.com")
    return accepted, relay


# ── what gets handed to the relay ───────────────────────────────────────────

def test_subject_dates_the_report_in_east_coast_time():
    #22:00 on the 27th in ET is already 02:00 on the 28th in UTC. the subject must say the 27th
    late_evening_et = datetime(2026, 7, 28, 2, 0, tzinfo=timezone.utc).astimezone(ET)
    relay = Mock(return_value=True)
    with patch("app.daily_update.digest_email.now_et", return_value=late_evening_et):
        with patch("app.daily_update.digest_email.send_email", relay):
            send_digest(MOD, [], "mod@example.com")
    assert relay.call_args.kwargs["subject"] == "Daily arXiv Moderator report 2026-07-27"


def test_only_that_moderators_address_is_on_it():
    _, relay = _send(Mock(return_value=True))
    assert relay.call_args.kwargs["to_emails"] == ["mod@example.com"]


def test_not_threaded_to_a_submission():
    #a digest isn't about one submission, so send_email gets no submission_id to thread on
    _, relay = _send(Mock(return_value=True))
    assert "submission_id" not in relay.call_args.kwargs


def test_an_empty_report_is_still_sent():
    accepted, relay = _send(Mock(return_value=True))
    assert accepted is True
    assert relay.call_count == 1


# ── failure handling ────────────────────────────────────────────────────────

def test_a_refused_send_is_reported_as_not_accepted():
    accepted, _ = _send(Mock(return_value=False))
    assert accepted is False


def test_a_raising_relay_is_swallowed():
    accepted, _ = _send(Mock(side_effect=RuntimeError("smtp down")))
    assert accepted is False


def test_a_failed_render_never_reaches_the_relay():
    relay = Mock(return_value=True)
    with patch("app.daily_update.digest_email.render_report", side_effect=ValueError("bad template")), \
         patch("app.daily_update.digest_email.send_email", relay):
        assert send_digest(MOD, [], "mod@example.com") is False
    relay.assert_not_called()


# ── retrying the relay ──────────────────────────────────────────────────────

def _send_no_sleep(relay: Mock) -> bool:
    """send_digest with the retry waits skipped"""
    with patch("app.daily_update.digest_email.time.sleep"), \
         patch("app.daily_update.digest_email.send_email", relay):
        return send_digest(MOD, [], "mod@example.com")

def test_a_dropped_connection_is_retried_and_can_succeed():
    relay = Mock(side_effect=[smtplib.SMTPServerDisconnected("bye"), True])
    assert _send_no_sleep(relay) is True #succeed
    assert relay.call_count == 2

def test_retries_run_out_and_the_digest_is_given_up_on():
    relay = Mock(side_effect=smtplib.SMTPServerDisconnected("bye"))
    assert _send_no_sleep(relay) is False #fails
    assert relay.call_count == SEND_ATTEMPTS

def test_real_relay_error_surfaces_when_attempts_run_out():
    relay = Mock(side_effect=smtplib.SMTPServerDisconnected("bye"))
    with patch("app.daily_update.digest_email.time.sleep"), \
         patch("app.daily_update.digest_email.send_email", relay):
        with pytest.raises(smtplib.SMTPServerDisconnected):
            _send_with_retry("mod@example.com", "text", "html")


def test_a_4xx_from_the_relay_is_retried():
    relay = Mock(side_effect=[smtplib.SMTPResponseException(451, b"try later"), True])
    assert _send_no_sleep(relay) is True
    assert relay.call_count == 2


def test_a_5xx_from_the_relay_is_not_retried():
    relay = Mock(side_effect=smtplib.SMTPResponseException(550, b"no such mailbox"))
    assert _send_no_sleep(relay) is False
    assert relay.call_count == 1


def test_bad_credentials_are_not_retried():
    #hammering a bad login can lock the account
    relay = Mock(side_effect=smtplib.SMTPAuthenticationError(535, b"nope"))
    assert _send_no_sleep(relay) is False
    assert relay.call_count == 1
