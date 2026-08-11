"""tests for the shared recipient-resolution chain: who_to_email -> get_recipient_ids_for_categories -> get_mod_emails

these need ToEmail dicts to work on, and the only builder that exists so far is
mod_actions' get_moderators() — so that is what they use. the behavior under test
here is shared, not mod_actions-specific.
"""
import pytest

from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.shared.moderators import who_to_email, get_recipient_ids_for_categories, get_mod_emails
from app.mod_actions.moderators import get_moderators


@pytest.mark.usefixtures("db_session")
def test_who_to_email_category_mod():
    archives, cats = get_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['q-bio.CB'], archives, cats)
    assert 246231 in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_includes_archive_mods():
    # q-bio.QM has no category-specific mods in data.sql — 246231 comes from archive only
    archives, cats = get_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['q-bio.QM'], archives, cats)
    assert 246231 in email
    assert 246231 in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_opt_out():
    archives, cats = get_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50001 not in email
    assert 50002 not in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_no_reply_to():
    archives, cats = get_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50003 in email
    assert 50003 not in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_replys():
    archives, cats = get_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50004 in email
    assert 50004 in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_category_optout_overrides_archive():
    # 77777 mods astro-ph archive but opted out of astro-ph.HE — should not appear via archive
    archives, cats = get_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['astro-ph.HE'], archives, cats)
    assert 77777 not in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_alias_category_mod():
    # 60001 mods q-fin.EC only, the alias of canonical econ.GN
    archives, cats = get_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['econ.GN'], archives, cats)
    assert 60001 in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_alias_archive_mod():
    # 246232 mods 'q-fin' archive-wide only -- not listed under econ, econ.GN, or q-fin.EC --
    # but 'q-fin' is the alias archive of econ.GN's alias category (q-fin.EC), so should still get emailed
    archives, cats = get_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['econ.GN'], archives, cats)
    assert 246232 in email
    assert 246232 in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_named_category_optout_cascades_to_alias_archive():
    # 60002 opts out at named category econ.GN and mods alias archive q-fin --
    # named-category opt-out should suppress the alias-archive inclusion too
    archives, cats = get_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['econ.GN'], archives, cats)
    assert 60002 not in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_no_mods_returns_empty():
    archives, cats = get_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['econ.EM'], archives, cats)
    assert len(email) == 0
    assert len(reply_to) == 0

@pytest.mark.usefixtures("db_session")
def test_get_recipient_ids_multi_category():
    archives, cats = get_moderators()
    categories = {CATEGORIES_ACTIVE['q-bio.CB'], CATEGORIES_ACTIVE['q-bio.NC'], CATEGORIES_ACTIVE['cs.AI'], CATEGORIES_ACTIVE['q-bio.MN']}
    per_cat, all_user_ids = get_recipient_ids_for_categories(categories, archives, cats)

    # 246231 moderates both categories and the q-bio archive
    assert 246231 in all_user_ids
    assert 246231 in per_cat['q-bio.CB'][0]
    assert 246231 in per_cat['q-bio.NC'][0]
    assert 246231 in per_cat['q-bio.MN'][0] #not a category they specifically moderate but still appears because of archive moderation

    # 681201 moderates q-bio.NC
    assert 681201 in all_user_ids
    assert 681201 in per_cat['q-bio.NC'][0]

    # 50004 moderates cs.AI and should appear
    assert 50004 in all_user_ids
    assert 50004 in per_cat['cs.AI'][0]

@pytest.mark.usefixtures("db_session")
def test_get_ids_reply_to_only():
    archives, cats = get_moderators()
    # 50001 in reply-to but not direct email
    per_cat, all_user_ids = get_recipient_ids_for_categories({CATEGORIES_ACTIVE['cs.AI']}, archives, cats)
    assert 50001 not in per_cat['cs.AI'][0]  # not in email set
    assert 50001 in per_cat['cs.AI'][1]      # in reply-to set
    assert 50001 in all_user_ids             # still needs email address looked up

@pytest.mark.usefixtures("db_session")
def test_get_recipient_ids_archive_optout_excluded():
    archives, cats = get_moderators()
    # 77777 mods astro-ph archive but fully opted out of astro-ph.HE
    per_cat, all_user_ids = get_recipient_ids_for_categories({CATEGORIES_ACTIVE['astro-ph.HE']}, archives, cats)
    assert 77777 not in per_cat['astro-ph.HE'][0]
    assert 77777 not in per_cat['astro-ph.HE'][1]
    assert 77777 not in all_user_ids


@pytest.mark.usefixtures("db_session")
def test_get_user_emails_returns_map():
    result = get_mod_emails({246231, 681201})
    assert result[246231].email == 'no-mail@example.com'
    assert result[246231].nickname == 'bbarker'
    assert result[246231].first_name == 'Brandon'
    assert result[246231].last_name == 'Barker'
    assert result[246231].display_name == 'Brandon Barker (bbarker)'
    assert result[681201].email == 'also-dont-mail@example.com'
    assert result[681201].nickname == 'shamsi'
    assert result[681201].display_name == 'Shams Brinn (shamsi)'

@pytest.mark.usefixtures("db_session")
def test_get_user_emails_empty_input():
    assert get_mod_emails(set()) == {}
