"""decides who gets a daily digest, and which submissions belong in it"""
import logging
from dataclasses import dataclass, field

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import ARCHIVES_ACTIVE, CATEGORIES_ACTIVE

from app.shared.moderators import Moderator, fetch_moderators

logger = logging.getLogger(__name__)


@dataclass
class DigestMod:
    """one moderator and what they moderate"""
    user_id: int
    labels: set[str] = field(default_factory=set)     #'cs.AI', 'astro-ph' — for the email header
    categories: set[str] = field(default_factory=set) #expanded ids, for matching submissions

    @property
    def header(self) -> str:
        """what they moderate, for the top of the email"""
        return " ".join(sorted(self.labels))


def _covered_categories(mod: Moderator) -> set[str]:
    """every category id a single moderator row covers, in every spelling it could be stored as"""

    if mod.category: #single cat mods
        cat = CATEGORIES_ACTIVE.get(mod.category)
        if cat is None:
            logger.warning(f"moderator {mod.user_id}: category {mod.category} is not active, skipping")
            return set()
        cats: list[Category] = [cat]

    else: #archive mods
        archive = ARCHIVES_ACTIVE.get(mod.archive)
        if archive is None:
            logger.warning(f"moderator {mod.user_id}: archive {mod.archive} is not active, skipping")
            return set()
        cats = archive.get_categories()

    #include aliases
    covered: set[str] = set()
    for cat in cats:
        covered.add(cat.id)
        if cat.alt_name:
            covered.add(cat.alt_name)
    return covered


def get_digest_recipients() -> dict[int, DigestMod]:
    """user_id -> what that moderator moderates, for everyone who wants a daily digest"""

    recipients: dict[int, DigestMod] = {}
    for mod_row in fetch_moderators():
        if not mod_row.daily_update:
            continue # doesnt want a daily update
        covered = _covered_categories(mod_row)
        if not covered:
            continue # somehow no categories
        entry = recipients.setdefault(mod_row.user_id, DigestMod(user_id=mod_row.user_id))
        entry.labels.add(mod_row.category or mod_row.archive) #what they signed up for
        entry.categories.update(covered) #everything included in it

    return recipients

