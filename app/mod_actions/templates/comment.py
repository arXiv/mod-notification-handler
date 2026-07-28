import html

from app.mod_actions.schema import SimplifiedNotification, CommentData
from app.shared.utils.dates import fmt_time


def render_comment_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: CommentData = change.data  
    when = fmt_time(change.time)
    text = (
        f"[{when}] {user_name} commented:\n"
        f"  {data.comment}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> commented:<br>\n"
        f"{html.escape(data.comment)}</p>\n"
    )
    return text, html_out
