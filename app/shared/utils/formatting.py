"""formatting helpers shared by all jobs' email templates"""
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings

logger = logging.getLogger(__name__)

ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)

MAX_AUTHORS = 7


def now_et() -> datetime:
    """the current moment in arXiv business time. every date and time in this project is ET,
    and the container has no TZ set, so never use date.today() or datetime.now() bare"""
    return datetime.now(ET)


def fmt_time(dt: datetime) -> str:
    """an aware time as arXiv business time

    A naive one is assumed UTC and warned about. Assuming is not the same as knowing: whoever
    read the value should attach its zone — see as_utc for database timestamps — because
    astimezone() on a naive datetime reads it in whatever zone the machine is in, UTC on Cloud
    Run and something else on a laptop.
    """
    if dt.tzinfo is None:
        logger.warning(f"naive datetime {dt} given to fmt_time, assuming UTC")
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(ET).strftime("%m-%d %H:%M %Z")


def truncate_authors(authors_str: str) -> str:
    """cut long author lists down"""
    parts = [a.strip() for a in authors_str.split(",")]
    if len(parts) > MAX_AUTHORS:
        return ", ".join(parts[:MAX_AUTHORS]) + ", ..."
    return ", ".join(parts)


