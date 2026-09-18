"""builds email content for new submission notifications

"""
from app.shared.submission import SubEmailData
from app.shared.templates import Rendered


def render_email(sub: SubEmailData) -> Rendered:
    """the text and html body of one new-submission email"""
    #TODO
    #TODO dont forget footer etc
    raise NotImplementedError("new_subs email layout not decided")
