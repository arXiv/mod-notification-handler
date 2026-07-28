"""date formatting shared by all jobs' email templates"""
from datetime import datetime
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings

_ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)


def fmt_time(dt: datetime) -> str:
    et = dt.astimezone(_ET)
    return et.strftime("%m-%d %H:%M %Z")
