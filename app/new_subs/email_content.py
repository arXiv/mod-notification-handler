"""builds email content for new submission notifications"""
from app.new_subs.submission import NewSubmission
from app.new_subs.templates.submission import render_submission
from app.shared.templates import Rendered, render_footer

SEPARATOR = "-" * 40 + "\n"


def render_email(sub: NewSubmission) -> Rendered:
    """the text and html body of one new-submission email"""
    sub_text, sub_html = render_submission(sub)
    footer_text, footer_html = render_footer()
    return Rendered(
        f"{sub_text}\n{SEPARATOR}{footer_text}",
        f"{sub_html}\n<hr>\n{footer_html}",
    )
