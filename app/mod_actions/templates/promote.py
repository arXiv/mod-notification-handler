from app.mod_actions.schema import SimplifiedNotification, PromoteData
from app.shared.utils.formatting import fmt_time
from app.shared.templates import Rendered


def render_promote_block(change: SimplifiedNotification, user_name: str) -> Rendered:
    data: PromoteData = change.data
    when = fmt_time(change.time)
    text = (
        f"[{when}] {user_name} promoted {data.category} to {data.promotion_type}:\n"
        f"  Change: {data.category_change}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> "
        f"promoted {data.category} to {data.promotion_type}<br>\n"
        f"Change: {data.category_change}</p>\n"
    )
    return Rendered(text, html_out)
