"""formatting helpers shared by all jobs' email templates"""
from datetime import datetime
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings

ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)

MAX_AUTHORS = 7


def now_et() -> datetime:
    """the current moment in arXiv business time. every date and time in this project is ET,
    and the container has no TZ set, so never use date.today() or datetime.now() bare"""
    return datetime.now(ET)


def fmt_time(dt: datetime) -> str:
    et = dt.astimezone(ET)
    return et.strftime("%m-%d %H:%M %Z")


def truncate_authors(authors_str: str) -> str:
    """cut long author lists down"""
    parts = [a.strip() for a in authors_str.split(",")]
    if len(parts) > MAX_AUTHORS:
        return ", ".join(parts[:MAX_AUTHORS]) + ", ..."
    return ", ".join(parts)


