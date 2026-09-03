"""when arXiv announces: the next mail time, and the days it skips entirely"""
import logging
from datetime import datetime
from functools import lru_cache
from typing import Optional
import requests
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Holiday

from app.shared.utils.formatting import now_et

LOCALTIME_URL = "https://arxiv.org/localtime"
TIMEOUT_SEC = 10

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def next_announce_time() -> Optional[datetime]:
    """when submissions still open now will be announced, or None if arxiv.org didn't answer

    Cached, so the digest run makes one request rather than one per email. Call it once at the
    start of the job so a slow response shows up there and not part way through sending.
    """
    try:
        response = requests.get(
            LOCALTIME_URL, headers={"Accept": "application/json"}, timeout=TIMEOUT_SEC
        )
        response.raise_for_status()
        times = response.json()

        return datetime.fromisoformat(times["next_mail"])

    except Exception:
        logger.exception(f"could not get the announce time from {LOCALTIME_URL}")
        return None


def is_holiday_today() -> bool:
    """whether today is an arXiv holiday: no freeze, no upcoming announcement, no digest
    Today is the East Coast date.
    """
    today = now_et().date()

    with Session() as session:
        found = session.execute(
            select(Holiday.freeze_skip_date).where(Holiday.freeze_skip_date == today)
        ).first()

    return found is not None
