
from app.schema import SimplifiedNotification, NewPropData
from app.email_content import _fmt_time


def render_new_prop_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: NewPropData = change.data  
    when = _fmt_time(change.time)
    text = (
        f"[{when}] {user_name} submitted a new category proposal:\n"
        f"  {data.msg}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> submitted a new category proposal:<br>\n"
        f"{data.msg}</p>\n"
    )
    return text, html_out
