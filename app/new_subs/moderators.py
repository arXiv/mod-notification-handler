"""decides who gets a new_subs email
"""
from app.shared.submission import SubEmailData


def get_recipients(sub: SubEmailData) -> tuple[list[str], list[str]]:
    """the addresses for one submission's email, as (to, reply_to)"""
    #TODO fetch based on sub categories + aliases and archives
    raise NotImplementedError("new_subs recipient rules not decided")
