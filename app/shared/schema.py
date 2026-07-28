"""data models shared by all jobs"""
from dataclasses import dataclass


@dataclass
class UserContact:
    email: str
    nickname: str
    first_name: str
    last_name: str

    @property
    def display_name(self) -> str:
        return f"{self.first_name} {self.last_name} ({self.nickname})"
