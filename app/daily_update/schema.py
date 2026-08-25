"""data shapes for the daily digest"""
from dataclasses import dataclass, field
from enum import Enum


class Section(str, Enum):
    """the parts of the report. TODO grouping/ordering not settled"""
    HOLD = "HOLD"
    NEW = "NEW"
    REPLACE = "REPLACE"
    CROSS = "CROSS"


SECTION_ORDER: list[Section] = [Section.HOLD, Section.NEW, Section.REPLACE, Section.CROSS]

#what each section is called in the email
SECTION_TITLES: dict[Section, str] = {
    Section.HOLD: "On Hold",
    Section.NEW: "New",
    Section.REPLACE: "Replacements",
    Section.CROSS: "Cross Lists",
}


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
