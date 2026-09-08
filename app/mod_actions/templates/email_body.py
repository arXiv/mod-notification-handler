from app.shared.templates import Rendered, render_footer


def render_body(
    sub_text: str,
    sub_html: str,
    change_texts: list[str],
    change_htmls: list[str],
) -> Rendered:
    footer_text, footer_html = render_footer()
    separator = "-" * 40 + "\n"
    body_text = (
        f"{sub_text}\n"
        f"{separator}"
        f"{separator.join(change_texts)}\n"
        f"{separator}"
        f"{footer_text}"
    )
    body_html = (
        f"{sub_html}\n"
        f"<hr>\n"
        f"{''.join(change_htmls)}\n"
        f"<hr>\n"
        f"{footer_html}"
    )
    return Rendered(body_text, body_html)
