from app.schema import SimplifiedNotification, PropRespData
from app.email_content import _fmt_time


def render_prop_resp_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: PropRespData = change.data 
    when = _fmt_time(change.time)
    text = (
        f"[{when}] {user_name} responded to category proposal(s):\n"
        f"  {data.responses}\n"
        f"  Change:     {data.category_change}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> responded to category proposal(s):<br>\n"
        f"{data.responses}<br>\n"
        f"Change: {data.category_change}</p>\n"
    )
    return text, html_out
