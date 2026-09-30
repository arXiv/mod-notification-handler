"""builds email to moderators about a new submission available

    ** warnings, if any **

    submit/submit_id submitted at: Submit_timestamp by Submitter_Name
    Review at: check link
    Title
    Authors (truncated)
    Categories
    System proposed primary
    Status
    Comments / Journal ref / DOI, each only when the submission has one
    Abstract
"""
import html

from arxiv.submission.statuses import STATUS_NAMES

from app.new_subs.submission import NewSubmission
from app.shared.templates import Rendered, check_submission_url
from app.shared.utils.formatting import fmt_time, truncate_authors


def format_warnings(sub: NewSubmission) -> Rendered:
    """the things a moderator should see before anything else. empty when there are none"""
    FIRST_TIME_WARNING = "Note: First submission from this submitter"
    FLAGGED_WARNING = "Warning: This submitter is flagged"
    warnings = []
    if sub.first_time_submitter:
        warnings.append(FIRST_TIME_WARNING)
    if sub.flagged_submitter:
        warnings.append(FLAGGED_WARNING)
    if not warnings:
        return Rendered("", "")

    text = "".join(f"** {warning} **\n" for warning in warnings) + "\n"
    html_out = "".join(f"<p><b>** {warning} **</b></p>\n" for warning in warnings)
    return Rendered(text, html_out)


def format_header(sub: NewSubmission) -> Rendered:
    """submit id, when it arrived, and who sent it. the time is left out when there isn't one"""
    submitter = sub.submitter_name or f"user {sub.submitter_id}"

    parts = [f"submit/{sub.submission_id}"]
    if sub.submit_time:
        parts.append(f"submitted at: {fmt_time(sub.submit_time)}")
    lead = " ".join(parts)
    return Rendered(f"{lead} by {submitter}", f"{lead} by {html.escape(submitter)}")


def _line(label: str, value: str) -> Rendered:
    """one labelled line, empty when the submission has no value for it"""
    if not value:
        return Rendered("", "")
    return Rendered(f"  {label}: {value}\n", f"<b>{label}:</b> {html.escape(value)}")


def _block(lines: list[Rendered]) -> Rendered:
    """a run of labelled lines, set apart from the block above it. empty when no line has a value"""
    lines = [line for line in lines if line.text]
    if not lines:
        return Rendered("", "")
    return Rendered(
        "\n" + "".join(line.text for line in lines),
        "<p>" + "<br>\n".join(line.html for line in lines) + "</p>\n",
    )


def render_submission(sub: NewSubmission) -> Rendered:
    """the whole body of one initial moderator email, as (text, html)"""

    #collect needed data
    warn_text, warn_html = format_warnings(sub)
    header_text, header_html = format_header(sub)
    title = sub.title or "(no title)"
    authors = truncate_authors(sub.authors) if sub.authors else "(no authors)"
    check_url = check_submission_url(sub.submission_id)

    system_text, system_html = _block([
        _line("Categories", sub.submission_categories),
        _line("System proposed primary", sub.system_proposed_primary),
        _line("Status", STATUS_NAMES.get(sub.status, str(sub.status))),
    ])
    details_text, details_html = _block([
        _line("Comments", sub.comments),
        _line("Journal ref", sub.journal_ref),
        _line("DOI", sub.doi),
    ])

    # fill in templates
    text = (
        f"{warn_text}"
        f"{header_text}\n"
        f"  Review at: {check_url}\n"
        f"  {title}\n"
        f"  {authors}\n"
        f"{system_text}"
        f"{details_text}"
    )

    html_out = (
        f"{warn_html}"
        f"<p>{header_html}<br>\n"
        f"<a href=\"{check_url}\">Review in arXiv Check</a><br>\n"
        f"<b>{html.escape(title)}</b><br>\n"
        f"{html.escape(authors)}</p>\n"
        f"{system_html}"
        f"{details_html}"
    )

    if sub.abstract:
        text += f"\nAbstract:\n{sub.abstract}\n"
        html_out += f"<p><b>Abstract:</b><br>\n{html.escape(sub.abstract)}</p>\n"

    return Rendered(text, html_out)
