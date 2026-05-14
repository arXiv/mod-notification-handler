CHECK_GUIDE_URL   = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/1312915466/arXiv+Check+Start+Guide"
CHECK_GUIDE_TITLE = "How to use Check"
HOW_TO_MOD_URL    = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/830767115/How+do+I+moderate+a+submission"
HOW_TO_MOD_TITLE  = "How to moderate"
MOD_HUB_URL       = "https://arxiv-org.atlassian.net/wiki/spaces/ModRes/pages/812580865/Moderator+Hub"
MOD_HUB_TITLE     = "Moderator Hub"


def render_email(
    sub_text: str,
    sub_html: str,
    change_texts: list[str],
    change_htmls: list[str],
) -> tuple[str, str]:
    separator = "-" * 40 + "\n"
    body_text = (
        f"{sub_text}\n"
        f"{separator}"
        f"{separator.join(change_texts)}\n"
        f"{separator}"
        f"{CHECK_GUIDE_TITLE}: {CHECK_GUIDE_URL} \n"
        f"{HOW_TO_MOD_TITLE}: {HOW_TO_MOD_URL} \n"
        f"{MOD_HUB_TITLE}: {MOD_HUB_URL} \n"
    )
    body_html = (
        f"{sub_html}\n"
        f"<hr>\n"
        f"{''.join(change_htmls)}\n"
        f"<hr>\n"
        f"<p>"
        f"<a href=\"{CHECK_GUIDE_URL}\">{CHECK_GUIDE_TITLE}</a> | "
        f"<a href=\"{HOW_TO_MOD_URL}\">{HOW_TO_MOD_TITLE}</a> | "
        f"<a href=\"{MOD_HUB_URL}\">{MOD_HUB_TITLE}</a>"
        f"</p>\n"
    )
    return body_text, body_html
