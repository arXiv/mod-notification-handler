
from app.schema import SimplifiedNotification, PromoteData
from app.email_content import _fmt_time


def render_promote_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: PromoteData = change.data
    when = _fmt_time(change.time)
    text = (
        f"[{when}] {user_name} promoted {data.category} to {data.promotion_type} :\n"
        f"  Change: {data.category_change}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> "
        f"promoted {data.category} to {data.promotion_type}<br>\n"
        f"Change: {data.category_change}</p>\n"
    )
    return text, html_out
