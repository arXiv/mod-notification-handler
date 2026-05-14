import pytest
from sqlalchemy import select

from arxiv.db.models import t_arXiv_moderators

from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.moderators import get_all_moderators, who_to_email, get_recipient_ids_for_categories, get_mod_emails

def test_db_can_read(db_session):
    result = db_session.execute(select(t_arXiv_moderators))
    rows = result.mappings().all()
    assert len(rows) > 0

@pytest.mark.usefixtures("db_session")
def test_archives_and_categories_separated():
    archives, cats = get_all_moderators()
    assert 'q-bio' in archives
    assert 'q-bio.NC' in cats
    assert 'q-bio' not in cats
    assert 'q-bio.NC' not in archives

@pytest.mark.usefixtures("db_session")
def test_category_key_uses_archive_dot_subject_class():
    _, cats = get_all_moderators()
    assert 'astro-ph.HE' in cats
    assert 'cs.AI' in cats

@pytest.mark.usefixtures("db_session")
def test_multiple_mods_aggregate_in_category():
    _, cats = get_all_moderators()
    # q-bio.NC has 4 moderators in data.sql
    assert cats['q-bio.NC'].send_to == {246231, 681201, 1234544, 246232}

@pytest.mark.usefixtures("db_session")
def test_mod_appears_in_multiple_archives():
    archives, _ = get_all_moderators()
    assert 9999 in archives['astro-ph'].send_to
    assert 9999 in archives['cond-mat'].send_to
    assert 9999 in archives['physics'].send_to

@pytest.mark.usefixtures("db_session")
def test_archive_mod_appears_in_both_archive_and_category():
    archives, cats = get_all_moderators()
    assert 246231 in archives['q-bio'].send_to
    assert 246231 in cats['q-bio.CB'].send_to
    assert 246231 in cats['q-bio.NC'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_email_goes_to_dont_send_to():
    _, cats = get_all_moderators()
    assert 50001 in cats['cs.AI'].dont_send_to
    assert 50001 not in cats['cs.AI'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_web_email_goes_to_dont_send_to():
    _, cats = get_all_moderators()
    assert 50002 in cats['cs.AI'].dont_send_to
    assert 50002 not in cats['cs.AI'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_reply_to_goes_to_dont_include_reply_to():
    _, cats = get_all_moderators()
    assert 50003 in cats['cs.AI'].dont_include_reply_to
    assert 50003 not in cats['cs.AI'].include_reply_to
    assert 50003 in cats['cs.AI'].send_to  # no_reply_to doesn't affect emailing

@pytest.mark.usefixtures("db_session")
def test_mod_who_wants_emails():
    archives, cats = get_all_moderators()
    assert 50004 in cats['cs.AI'].send_to
    assert 50004 in cats['cs.AI'].include_reply_to
    assert 50004 in archives['cs'].send_to
    assert 50004 in archives['cs'].include_reply_to

# who_to_email tests

@pytest.mark.usefixtures("db_session")
def test_who_to_email_category_mod():
    archives, cats = get_all_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['q-bio.CB'], archives, cats)
    assert 246231 in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_includes_archive_mods():
    # q-bio.QM has no category-specific mods in data.sql — 246231 comes from archive only
    archives, cats = get_all_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['q-bio.QM'], archives, cats)
    assert 246231 in email
    assert 246231 in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_opt_out():
    archives, cats = get_all_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50001 not in email
    assert 50002 not in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_no_reply_to():
    archives, cats = get_all_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50003 in email
    assert 50003 not in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_replys():
    archives, cats = get_all_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['cs.AI'], archives, cats)
    assert 50004 in email
    assert 50004 in reply_to

@pytest.mark.usefixtures("db_session")
def test_who_to_email_category_optout_overrides_archive():
    # 77777 mods astro-ph archive but opted out of astro-ph.HE — should not appear via archive
    archives, cats = get_all_moderators()
    email, _ = who_to_email(CATEGORIES_ACTIVE['astro-ph.HE'], archives, cats)
    assert 77777 not in email

@pytest.mark.usefixtures("db_session")
def test_who_to_email_no_mods_returns_empty():
    archives, cats = get_all_moderators()
    email, reply_to = who_to_email(CATEGORIES_ACTIVE['econ.EM'], archives, cats)
    assert len(email) == 0
    assert len(reply_to) == 0

@pytest.mark.usefixtures("db_session")
def test_get_recipient_ids_multi_category():
    archives, cats = get_all_moderators()
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
    archives, cats = get_all_moderators()
    # 50001 in reply-to but not direct email
    per_cat, all_user_ids = get_recipient_ids_for_categories({CATEGORIES_ACTIVE['cs.AI']}, archives, cats)
    assert 50001 not in per_cat['cs.AI'][0]  # not in email set
    assert 50001 in per_cat['cs.AI'][1]      # in reply-to set
    assert 50001 in all_user_ids             # still needs email address looked up

@pytest.mark.usefixtures("db_session")
def test_get_recipient_ids_archive_optout_excluded():
    archives, cats = get_all_moderators()
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
