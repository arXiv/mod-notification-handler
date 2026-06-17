import html

from app.schema import SimplifiedNotification, CommentData
from app.email_content import _fmt_time


def render_comment_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: CommentData = change.data  
    when = _fmt_time(change.time)
    text = (
        f"[{when}] {user_name} added a comment:\n"
        f"  {data.comment}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> added a comment:<br>\n"
        f"{html.escape(data.comment)}</p>\n"
    )
    return text, html_out
