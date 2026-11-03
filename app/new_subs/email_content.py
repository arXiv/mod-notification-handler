"""builds email content for new submission notifications

"""
from app.shared.submission import SubmissionBase
from app.shared.templates import Rendered


def render_email(sub: SubmissionBase) -> Rendered:
    """the text and html body of one new-submission email"""
    #TODO
    #TODO dont forget footer etc
    raise NotImplementedError("new_subs email layout not decided")
