"""one submission's entry in the daily digest

    Submit_timestamp Primary Secondary Submitter_Name submit/submit_id
    Title (links to Check)
    Authors (truncated)
    Proposals: primary proposals, secondary proposals
"""
import html

from app.daily_update.submissions import OpenSubmission
from app.shared.templates import Rendered, check_submission_url
from app.shared.utils.formatting import fmt_time, truncate_authors

# FORMATTING HELPERS

def format_timestamp(sub: OpenSubmission) -> str:
    return fmt_time(sub.submit_time) if sub.submit_time else "(no submit time)"

def format_categories(sub: OpenSubmission) -> Rendered:
    """returns text, html """
    #highlight primary category
    primary = sub.primary_category
    if primary:
        text_primary, html_primary = primary, f"<b>{primary}</b>"
    else:
        text_primary, html_primary = "no primary", "<b>no primary</b>"

    parts = sub.secondary_categories
    return Rendered(" ".join([text_primary] + parts), " ".join([html_primary] + parts))

def format_proposals(sub: OpenSubmission) -> str:
    """unresolved proposals, primary and secondary listed apart, alphabetical within each"""
    if not sub.proposals:
        return "Proposals: none"

    output = ""
    if sub.proposals.primary:
        output += "Primary proposals: " + ", ".join(sorted(sub.proposals.primary))

    if sub.proposals.secondary:
        if output: #only needs a separator when the primary group went first
            output += "; "
        output += "Secondary proposals: " + ", ".join(sorted(sub.proposals.secondary))

    return output


#CREATE ENTRY

def render_entry(sub: OpenSubmission) -> Rendered:
    """one submission's worth of the report, as (text, html)"""
    when = format_timestamp(sub)
    cats_text, cats_html = format_categories(sub)
    submitter = sub.submitter_name or f"user {sub.submitter_id}"
    title = sub.title or "(no title)"
    authors = truncate_authors(sub.authors) if sub.authors else "(no authors)"
    check_url = check_submission_url(sub.submission_id)
    activity = format_proposals(sub)

    #backup format
    text = (
        f"  {when}   {cats_text}   {submitter}   submit/{sub.submission_id}\n"
        f"    {title}\n"
        f"    Review at: {check_url}\n"
        f"    {authors}\n"
        f"    {activity}\n"
    )

    #prefered format
    html_out = (
        f"<p>{when} &nbsp; {cats_html} &nbsp; {html.escape(submitter)} &nbsp; submit/{sub.submission_id}<br>\n"
        f"<a href=\"{check_url}\">{html.escape(title)}</a><br>\n"
        f"{html.escape(authors)}<br>\n"
        f"{activity}</p>\n"
    )

    return Rendered(text, html_out)
