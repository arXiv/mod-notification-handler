"""tests for mod_actions' get_moderators() — this job's email-preference flag rules

the shared layer downstream of the ToEmail dicts is covered in tests/shared/test_recipients.py
"""
import pytest

from app.mod_actions.moderators import get_moderators


@pytest.mark.usefixtures("db_session")
def test_archives_and_categories_separated():
    archives, cats = get_moderators()
    assert 'q-bio' in archives
    assert 'q-bio.NC' in cats
    assert 'q-bio' not in cats
    assert 'q-bio.NC' not in archives

@pytest.mark.usefixtures("db_session")
def test_category_key_uses_archive_dot_subject_class():
    _, cats = get_moderators()
    assert 'astro-ph.HE' in cats
    assert 'cs.AI' in cats

@pytest.mark.usefixtures("db_session")
def test_multiple_mods_aggregate_in_category():
    _, cats = get_moderators()
    # q-bio.NC has 4 moderators in data.sql
    assert cats['q-bio.NC'].send_to == {246231, 681201, 1234544, 246232}

@pytest.mark.usefixtures("db_session")
def test_mod_appears_in_multiple_archives():
    archives, _ = get_moderators()
    assert 9999 in archives['astro-ph'].send_to
    assert 9999 in archives['cond-mat'].send_to
    assert 9999 in archives['physics'].send_to

@pytest.mark.usefixtures("db_session")
def test_archive_mod_appears_in_both_archive_and_category():
    archives, cats = get_moderators()
    assert 246231 in archives['q-bio'].send_to
    assert 246231 in cats['q-bio.CB'].send_to
    assert 246231 in cats['q-bio.NC'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_email_goes_to_dont_send_to():
    _, cats = get_moderators()
    assert 50001 in cats['cs.AI'].dont_send_to
    assert 50001 not in cats['cs.AI'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_web_email_goes_to_dont_send_to():
    _, cats = get_moderators()
    assert 50002 in cats['cs.AI'].dont_send_to
    assert 50002 not in cats['cs.AI'].send_to

@pytest.mark.usefixtures("db_session")
def test_no_reply_to_goes_to_dont_include_reply_to():
    _, cats = get_moderators()
    assert 50003 in cats['cs.AI'].dont_include_reply_to
    assert 50003 not in cats['cs.AI'].include_reply_to
    assert 50003 in cats['cs.AI'].send_to  # no_reply_to doesn't affect emailing

@pytest.mark.usefixtures("db_session")
def test_mod_who_wants_emails():
    archives, cats = get_moderators()
    assert 50004 in cats['cs.AI'].send_to
    assert 50004 in cats['cs.AI'].include_reply_to
    assert 50004 in archives['cs'].send_to
    assert 50004 in archives['cs'].include_reply_to
