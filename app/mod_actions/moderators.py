"""decides who gets a mod_actions email

Job-specific rules: a moderator is not emailed if they set either no_email or
no_web_email. daily_update has no effect here — these notifications go out as
the actions happen.
"""
from app.shared.moderators import ToEmail, fetch_moderators


def get_moderators() -> tuple[dict[str, ToEmail], dict[str, ToEmail]]:
    """fetch mod data from db. process into who to email for categories"""

    moderators = fetch_moderators()

    #who should get emailed
    all_cats: dict[str, ToEmail] ={}
    all_archives: dict[str, ToEmail] ={}

    for mod in moderators:
        # is this a category or archive entry
        if mod.category:
            store = all_cats
            key = mod.category
        else:
            store = all_archives
            key = mod.archive

        entry: ToEmail=store.get(key, ToEmail())

        #email pref
        if mod.no_email or mod.no_web_email:
            entry.dont_send_to.add(mod.user_id)
        else:
            entry.send_to.add(mod.user_id)

        # reply to pref
        if mod.no_reply_to:
            entry.dont_include_reply_to.add(mod.user_id)
        else:
            entry.include_reply_to.add(mod.user_id)

        store[key] = entry

    return all_archives, all_cats
