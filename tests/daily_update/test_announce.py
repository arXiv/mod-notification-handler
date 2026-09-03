"""tests for reading the next announcement time off arxiv.org/localtime"""
from datetime import date, datetime, timezone
from unittest.mock import Mock, patch

import pytest
import requests

from app.shared.utils.formatting import ET
from app.daily_update import announce
from app.daily_update.announce import is_holiday_today
from app.daily_update.main import main

#the job runs after the freeze, while moderators are still working the submissions that go
#out in that evening's mail. next_mail is the one they are racing
LOCALTIME = {
    "next_freeze": "2026-09-04T18:00:00+00:00",
    "next_mail": "2026-09-04T00:00:00+00:00",
    "subsequent_mail": "2026-09-07T00:00:00+00:00",
    "arxiv_tz": "EDT",
}


@pytest.fixture(autouse=True)
def announce_time():
    """this module tests the real fetch, so shadow the package-wide stub"""
    yield


@pytest.fixture(autouse=True)
def _uncached():
    """the real function memoises, so each test starts from an empty cache"""
    announce.next_announce_time.cache_clear()
    yield
    announce.next_announce_time.cache_clear()


def _responds(payload=None, exc=None) -> Mock:
    if exc:
        return Mock(side_effect=exc)
    response = Mock()
    response.json.return_value = payload
    return Mock(return_value=response)


def test_reads_the_next_mail_time():
    with patch("app.daily_update.announce.requests.get", _responds(LOCALTIME)):
        assert announce.next_announce_time() == datetime(2026, 9, 4, tzinfo=timezone.utc)


def test_one_request_per_run_however_many_emails():
    getter = _responds(LOCALTIME)
    with patch("app.daily_update.announce.requests.get", getter):
        for _ in range(5):
            announce.next_announce_time()
    assert getter.call_count == 1


def test_a_failed_request_is_not_fatal():
    with patch("app.daily_update.announce.requests.get",
               _responds(exc=requests.RequestException("arxiv.org is down"))):
        assert announce.next_announce_time() is None


def test_a_response_missing_fields_is_not_fatal():
    with patch("app.daily_update.announce.requests.get", _responds({"arxiv_tz": "EDT"})):
        assert announce.next_announce_time() is None


# ── holidays ────────────────────────────────────────────────────────────────

def _on(day: date):
    """run as if today were day, in ET"""
    return patch("app.daily_update.announce.now_et",
                 return_value=datetime(day.year, day.month, day.day, 12, tzinfo=ET))


@pytest.mark.usefixtures("db_session")
def test_a_seeded_holiday_is_one():
    with _on(date(2026, 9, 7)):   #labor day
        assert is_holiday_today()
    with _on(date(2026, 12, 25)):
        assert is_holiday_today()


@pytest.mark.usefixtures("db_session")
def test_an_ordinary_day_is_not():
    with _on(date(2026, 7, 27)):
        assert not is_holiday_today()


@pytest.mark.usefixtures("db_session")
def test_the_date_checked_is_east_coast_not_utc():
    #23:00 ET on the 6th is already the 7th in UTC. labor day is the 7th, so a utc date would
    #wrongly skip the digest the evening before
    evening_before = datetime(2026, 9, 7, 3, 0, tzinfo=timezone.utc)
    with patch("app.daily_update.announce.now_et", return_value=evening_before.astimezone(ET)):
        assert not is_holiday_today()


@pytest.mark.usefixtures("db_session")
def test_the_job_sends_nothing_on_a_holiday():
    sent = patch("app.daily_update.main.send_daily_reports")
    with patch("app.daily_update.main.email_config_ok", return_value=True), \
         patch("app.daily_update.main.is_holiday_today", return_value=True), sent as send:
        main()
    send.assert_not_called()


@pytest.mark.usefixtures("db_session")
def test_the_job_runs_on_an_ordinary_day():
    with patch("app.daily_update.main.email_config_ok", return_value=True), \
         patch("app.daily_update.main.is_holiday_today", return_value=False), \
         patch("app.daily_update.main.send_daily_reports") as send:
        main()
    send.assert_called_once()
