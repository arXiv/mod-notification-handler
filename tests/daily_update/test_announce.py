"""tests for reading the next announcement time off arxiv.org/localtime"""
from datetime import datetime, timezone
from unittest.mock import Mock, patch

import pytest
import requests

from app.daily_update import announce

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
