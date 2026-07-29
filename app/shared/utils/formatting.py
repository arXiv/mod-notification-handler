"""formatting helpers shared by all jobs' email templates"""
from datetime import datetime
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings

from app.shared.utils.taxonomy import ALIAS_BY_CANONICAL

_ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)


def fmt_time(dt: datetime) -> str:
    et = dt.astimezone(_ET)
    return et.strftime("%m-%d %H:%M %Z")


def build_category_string(cats: list[tuple[str, int]]) -> str:
    """Format [(category, is_primary), ...] into 'cs.LG (primary), cs.AI'."""
    primary = "-" #TODO change to no primary when more off of legacy system
    secondaries: set[str] = set()
    for cat_id, is_primary in cats:
        if is_primary:
            primary = cat_id
        else:
            secondaries.add(cat_id)
        #catch aliases
        if cat_id in ALIAS_BY_CANONICAL:
            secondaries.add(ALIAS_BY_CANONICAL[cat_id])
    parts = [f"{primary}"] + sorted(secondaries)
    return " ".join(parts)
