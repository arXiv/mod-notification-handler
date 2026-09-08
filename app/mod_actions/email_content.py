"""builds email content for submission notifications"""
from app.shared.schema import UserContact
from app.shared.submission import SubEmailData
from app.mod_actions.schema import SimplifiedNotification, CommentData, PromoteData, NewPropData, PropRespData, CategoryRejectionData, EmailTask

from app.mod_actions.templates.comment import render_comment_block
from app.mod_actions.templates.promote import render_promote_block
from app.mod_actions.templates.new_prop import render_new_prop_block
from app.mod_actions.templates.prop_resp import render_prop_resp_block
from app.mod_actions.templates.category_rejection import render_category_rejection_block
from app.mod_actions.templates.submission import render_submission_block
from app.mod_actions.templates.email_body import render_body
from app.shared.templates import Rendered


def render_change_block(change: SimplifiedNotification, user_name: str) -> Rendered:
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
        case CategoryRejectionData():
            return render_category_rejection_block(change, user_name)
        case _:
            raise ValueError(f"unknown change data type: {type(change.data)}")


def render_email(task: EmailTask, sub: SubEmailData, ids_to_contact: dict[int, UserContact]) -> Rendered:
    sub_text, sub_html = render_submission_block(sub)
    change_texts, change_htmls = [], []
    for change in sorted(task.notifications.changes, key=lambda c: c.time):
        contact = ids_to_contact.get(change.user_id)
        name = contact.display_name if contact else f"user {change.user_id}"
        ct, ch = render_change_block(change, name)
        change_texts.append(ct)
        change_htmls.append(ch)
    return render_body(sub_text, sub_html, change_texts, change_htmls)

