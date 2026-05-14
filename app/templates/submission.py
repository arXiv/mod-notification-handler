import html

from arxiv.submission.statuses import STATUS_NAMES

from app.schema import SubEmailData

CHECK_SUBMISSION_URL = "https://check.arxiv.org/submit/{submission_id}"


def render_submission_block(sub: SubEmailData) -> tuple[str, str]:
    status_label = STATUS_NAMES.get(sub.status, str(sub.status))
    cat_list = sub.submission_categories or "(none)"
    check_url = CHECK_SUBMISSION_URL.format(submission_id=sub.submission_id)
    title = sub.title or "(no title)"
    authors = sub.authors or "(no authors)"

    text = (
        f"Submission: submit/{sub.submission_id}\n"
        f"Title:      {title}\n"
        f"Authors:    {authors}\n"
        f"Status:     {status_label}\n"
        f"Current Categories: {cat_list}\n"
        f"View in Check:      {check_url}\n"
    )
    html_out = (
        f"<p><strong>Submission:</strong> submit/{sub.submission_id}<br>\n"
        f"<strong>Title:</strong> {html.escape(title)}<br>\n"
        f"<strong>Authors:</strong> {html.escape(authors)}<br>\n"
        f"<strong>Status:</strong> {status_label}<br>\n"
        f"<strong>Current Categories:</strong> {cat_list}<br>\n"
        f"<strong>View in Check:</strong> <a href=\"{check_url}\">{check_url}</a></p>\n"
    )
    return text, html_out
