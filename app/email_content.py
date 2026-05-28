"""builds email content for submission notifications"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import select

from arxiv.db import Session
from arxiv.db.models import Submission, SubmissionCategory
from arxiv.taxonomy.definitions import CATEGORY_ALIASES

from app.schema import SubEmailData, SimplifiedNotification, CommentData, PromoteData, NewPropData, PropRespData, EmailTask, UserContact

_ET = ZoneInfo("America/New_York")
def _fmt_time(dt: datetime) -> str:
    et = dt.astimezone(_ET)
    return et.strftime("%m-%d %H:%M ET")

from app.templates.comment import render_comment_block
from app.templates.promote import render_promote_block
from app.templates.new_prop import render_new_prop_block
from app.templates.prop_resp import render_prop_resp_block
from app.templates.submission import render_submission_block
from app.templates.email_body import render_body


_ALIAS_BY_CANONICAL = {v: k for k, v in CATEGORY_ALIASES.items()}


def _build_category_string(cats: list[tuple[str, int]]) -> str:
    """Format [(category, is_primary), ...] into 'cs.LG (primary), cs.AI'."""
    primary = "no primary"
    secondaries: set[str] = set()
    for cat_id, is_primary in cats:
        if is_primary:
            primary = cat_id
        else:
            secondaries.add(cat_id)
        #catch aliases
        if cat_id in _ALIAS_BY_CANONICAL:
            secondaries.add(_ALIAS_BY_CANONICAL[cat_id])
    parts = [f"{primary}"] + sorted(secondaries)
    return " ".join(parts)


def get_submission_info(submission_ids: set[int]) -> dict[int, SubEmailData]:
    """Fetch submission fields needed for email rendering. Returns only found rows."""
    if not submission_ids:
        return {}
    with Session() as session:
        #get general submission data
        rows = session.execute(
            select(
                Submission.submission_id,
                Submission.title,
                Submission.authors,
                Submission.status,
                Submission.submitter_name,
                Submission.submitter_id,
            ).where(Submission.submission_id.in_(submission_ids))
        ).all()

        #get and consolidate category data
        cat_rows = session.execute(
            select(SubmissionCategory.submission_id, SubmissionCategory.category, SubmissionCategory.is_primary)
            .where(SubmissionCategory.submission_id.in_(submission_ids))
        ).all()

        cats_by_sub: dict[int, list[tuple[str, int]]] = {}
        for cr in cat_rows:
            cats_by_sub.setdefault(cr.submission_id, []).append((cr.category, cr.is_primary))

        return {
            row.submission_id: SubEmailData(
                submission_id=row.submission_id,
                title=row.title or "",
                authors=row.authors or "",
                status=row.status,
                submitter_name=row.submitter_name or "",
                submitter_id=row.submitter_id or 0,
                submission_categories=_build_category_string(cats_by_sub.get(row.submission_id, [])),
            )
            for row in rows
        }


def render_change_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    """Dispatch to the correct per-change render function."""
    match change.data:
        case CommentData():
            return render_comment_block(change, user_name)
        case PromoteData():
            return render_promote_block(change, user_name)
        case NewPropData():
            return render_new_prop_block(change, user_name)
        case PropRespData():
            return render_prop_resp_block(change, user_name)
        case _:
            raise ValueError(f"unknown change data type: {type(change.data)}")


def render_email(task: EmailTask, sub: SubEmailData, ids_to_contact: dict[int, UserContact]) -> tuple[str, str]:
    sub_text, sub_html = render_submission_block(sub)
    change_texts, change_htmls = [], []
    for change in sorted(task.notifications.changes, key=lambda c: c.time, reverse=True):
        contact = ids_to_contact.get(change.user_id)
        name = contact.display_name if contact else f"user {change.user_id}"
        ct, ch = render_change_block(change, name)
        change_texts.append(ct)
        change_htmls.append(ch)
    return render_body(sub_text, sub_html, change_texts, change_htmls)

