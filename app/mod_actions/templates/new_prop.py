
from app.mod_actions.schema import SimplifiedNotification, NewPropData
from app.shared.utils.formatting import fmt_time


def render_new_prop_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: NewPropData = change.data  
    when = fmt_time(change.time)
    text = (
        f"[{when}] {user_name} category proposal:\n"
        f"  {data.msg}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> category proposal:<br>\n"
        f"{data.msg}</p>\n"
    )
    return text, html_out
