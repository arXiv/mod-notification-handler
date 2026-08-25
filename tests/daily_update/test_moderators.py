"""tests for who gets a digest, against the seeded database"""
from unittest.mock import patch
import pytest

from app.shared.moderators import Moderator
from app.daily_update.moderators import get_digest_recipients

# ── get_digest_recipients ───────────────────────────────────────────────────

@pytest.mark.usefixtures("db_session")
def test_only_moderators_who_asked_for_a_digest():
    recipients = get_digest_recipients()
    assert set(recipients.keys()) == {55001, 55002, 55003, 55004, 55005, 55006}
    assert 50004 not in get_digest_recipients() #no daily_update    

@pytest.mark.usefixtures("db_session")
def test_category_moderator_covers_one_category():
    mod = get_digest_recipients()[55001]
    assert mod.labels == {"cs.AI"}
    assert "cs.AI" in mod.categories
    assert "cs.LG" not in mod.categories


@pytest.mark.usefixtures("db_session")
def test_archive_moderator_covers_every_category_in_the_archive():
    mod = get_digest_recipients()[55002]
    assert mod.labels == {"astro-ph"}
    assert {"astro-ph.HE", "astro-ph.CO"} <= mod.categories


@pytest.mark.usefixtures("db_session")
def test_canonical_moderator_also_covers_the_alias():
    #55003's row says econ.GN; q-fin.EC is its alias and submissions may be stored under it
    mod = get_digest_recipients()[55003]
    assert mod.labels == {"econ.GN"}
    assert {"econ.GN", "q-fin.EC"} <= mod.categories

