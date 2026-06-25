import html
from zoneinfo import ZoneInfo

from arxiv.config import settings as arxiv_settings
from arxiv.submission.statuses import STATUS_NAMES

from app.schema import SubEmailData

CHECK_SUBMISSION_URL = "https://check.arxiv.org/submit/{submission_id}"
_ET = ZoneInfo(arxiv_settings.ARXIV_BUSINESS_TZ)
MAX_AUTHORS = 15


def truncate_authors(authors_str: str) -> str:
    parts = [a.strip() for a in authors_str.split(",")]
    if len(parts) > MAX_AUTHORS:
        return ", ".join(parts[:MAX_AUTHORS]) + ", ..."
    return ", ".join(parts)


def render_submission_block(sub: SubEmailData) -> tuple[str, str]:
    status_label = STATUS_NAMES.get(sub.status, str(sub.status))
    raw = sub.submission_categories or "(none)"
    cat_list = "no primary" + raw[1:] if (raw == "-" or raw.startswith("- ")) else raw
    check_url = CHECK_SUBMISSION_URL.format(submission_id=sub.submission_id)
    title = sub.title or "(no title)"
    authors = truncate_authors(sub.authors) if sub.authors else "(no authors)"

    submit_time_str = (
        sub.submit_time.astimezone(_ET).strftime("%Y-%m-%d %H:%M %Z")
        if sub.submit_time else None
    )

    text = (
        f"Submission: submit/{sub.submission_id} | {check_url}\n"
        f"Title:      {title}\n"
        f"Authors:    {authors}\n"
        f"Status:     {status_label}\n"
        f"Current Categories: {cat_list}\n"
    )
    if submit_time_str:
        text += f"Submitted:  {submit_time_str}\n"

    html_out = (
        f"<p><strong>Submission:</strong> submit/{sub.submission_id} | <a href=\"{check_url}\">{check_url}</a><br>\n"
        f"<strong>Title:</strong> {html.escape(title)}<br>\n"
        f"<strong>Authors:</strong> {html.escape(authors)}<br>\n"
        f"<strong>Status:</strong> {status_label}<br>\n"
        f"<strong>Current Categories:</strong> {cat_list}"
    )
    if submit_time_str:
        html_out += f"<br>\n<strong>Submitted:</strong> {submit_time_str}"
    html_out += "</p>\n"
    return text, html_out
