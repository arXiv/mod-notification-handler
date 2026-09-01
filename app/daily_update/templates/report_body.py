"""assembles a whole digest: header, the sections, footer"""
from enum import Enum

from app.shared.templates import Rendered, render_footer

MOD_TODO_URL = "https://check.arxiv.org/q/todo"
MOD_TODO_TITLE = "Your moderation todo queue"

ANNOUNCE_TIME = "(announce time not yet available)" #TODO calculate publish time
ANNOUNCE_LINE = (
    "If no further actions are taken, all submissions below not currently on hold "
    f"will be announced at {ANNOUNCE_TIME}."
)


class Section(str, Enum):
    """the parts of the report, listed in the order they appear. the value is the heading used in the email."""
    HOLD = "On Hold"
    NEW = "New"
    CROSS = "Cross Lists"

NOTHING_TO_REPORT = "You have no new activity or submissions on Hold today!"
EMPTY_SECTION = "none"

def render_header(what_they_moderate: str) -> Rendered:
    """who the report is for, and the link to their queue"""
    text = (
        f"Daily moderator report for {what_they_moderate}\n\n"
        f"{ANNOUNCE_LINE}\n\n"
        f"{MOD_TODO_TITLE}: {MOD_TODO_URL}\n"
    )
    html_out = (
        f"<p>Daily moderator report for {what_they_moderate}</p>\n"
        f"<p>{ANNOUNCE_LINE}</p>\n"
        f"<p><a href=\"{MOD_TODO_URL}\">{MOD_TODO_TITLE}</a></p>\n"
    )
    return Rendered(text, html_out)


def render_section(section: Section, entries: list[Rendered]) -> Rendered:
    """one section and its entries, or a placeholder when it's empty"""
    title = section.value
    if entries:
        body_text = "".join(entry.text for entry in entries)
        body_html = "".join(entry.html for entry in entries)
    else:
        body_text = f"  {EMPTY_SECTION}\n"
        body_html = f"<p>{EMPTY_SECTION}</p>\n"
    return Rendered(f"\n{title}:\n{body_text}", f"<h3>{title}:</h3>\n{body_html}")


def render_body(
    what_they_moderate: str,
    entries_by_section: dict[Section, list[Rendered]],
) -> Rendered:
    """the whole email for one group of moderators. an empty report is still a report"""
    header_text, header_html = render_header(what_they_moderate)
    footer_text, footer_html = render_footer()

    if not any(entries_by_section.values()):
        return Rendered(
            f"{header_text}\n{NOTHING_TO_REPORT}\n\n{footer_text}",
            f"{header_html}<p>{NOTHING_TO_REPORT}</p>\n<hr>\n{footer_html}",
        )

    body_text, body_html = "", ""
    for section in Section:
        section_text, section_html = render_section(section, entries_by_section.get(section, []))
        body_text += section_text
        body_html += section_html

    return Rendered(
        f"{header_text}{body_text}\n{footer_text}",
        f"{header_html}{body_html}<hr>\n{footer_html}",
    )
