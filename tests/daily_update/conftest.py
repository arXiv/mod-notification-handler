"""daily_update test setup"""
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

#2026-09-04 00:00 UTC is 09-03 20:00 EDT
ANNOUNCE_AT = datetime(2026, 9, 4, 0, 0, tzinfo=timezone.utc)


@pytest.fixture(autouse=True)
def announce_time():
    """no test reaches arxiv.org/localtime. every digest is dated from a fixed time"""
    with patch("app.daily_update.announce.next_announce_time", return_value=ANNOUNCE_AT):
        yield ANNOUNCE_AT
