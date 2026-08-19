from app.mod_actions.schema import SimplifiedNotification, CategoryRejectionData
from app.shared.utils.formatting import fmt_time

_REJECTION_LABELS = {
    "reject": "removed from submission",
    "accept_secondary": "demoted to secondary",
    "cross_submission": "removed from cross submission",
}


def render_category_rejection_block(change: SimplifiedNotification, user_name: str) -> tuple[str, str]:
    data: CategoryRejectionData = change.data
    when = fmt_time(change.time)
    label = _REJECTION_LABELS.get(data.rejection_type, data.rejection_type)
    text = (
        f"[{when}] {user_name} rejected {data.category} ({label}):\n"
        f"  Change: {data.category_change}\n"
    )
    html_out = (
        f"<p><strong>[{when}] {user_name}</strong> "
        f"rejected {data.category} ({label})<br>\n"
        f"Change: {data.category_change}</p>\n"
    )
    return text, html_out
