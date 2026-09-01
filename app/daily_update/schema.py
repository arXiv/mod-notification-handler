"""data shapes for the daily digest"""
from dataclasses import dataclass, field


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
