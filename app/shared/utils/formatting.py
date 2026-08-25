"""formatting helpers shared by all jobs' email templates"""
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings

from app.shared.utils.taxonomy import ALIAS_BY_CANONICAL

_ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)

MAX_AUTHORS = 7


def fmt_time(dt: datetime) -> str:
    et = dt.astimezone(_ET)
    return et.strftime("%m-%d %H:%M %Z")


def truncate_authors(authors_str: str) -> str:
    """cut long author lists down"""
    parts = [a.strip() for a in authors_str.split(",")]
    if len(parts) > MAX_AUTHORS:
        return ", ".join(parts[:MAX_AUTHORS]) + ", ..."
    return ", ".join(parts)


def split_categories(cats: list[tuple[str, int]]) -> tuple[Optional[str], list[str]]:
    """Split [(category, is_primary), ...] into (primary, sorted secondaries). primary is
    None when the submission has no primary row."""
    primary: Optional[str] = None
    secondaries: set[str] = set()
    for cat_id, is_primary in cats:
        if is_primary:
            primary = cat_id
        else:
            secondaries.add(cat_id)
        #catch aliases
        if cat_id in ALIAS_BY_CANONICAL:
            secondaries.add(ALIAS_BY_CANONICAL[cat_id])
    return primary, sorted(secondaries)


def build_category_string(cats: list[tuple[str, int]]) -> str:
    """Format [(category, is_primary), ...] into 'cs.LG (primary), cs.AI'."""
    primary, secondaries = split_categories(cats)
    primary = primary or "-" #TODO change to no primary when more off of legacy system
    return " ".join([primary] + secondaries)
