"""tests for who gets a new_subs email
"""
import pytest

from app.new_subs.moderators import get_recipients
from app.shared.submission import SubmissionBase, SubmissionCat


def _sub(*categories: str, sub_type: str = "new", announced: tuple[str, ...] = ()) -> SubmissionBase:
    return SubmissionBase(
        submission_id=1,
        title="A Title",
        authors="An Author",
        status=1,
        submitter_name="Pippin Otter",
        submitter_id=246234,
        sub_type=sub_type,
        categories=[
            SubmissionCat(category=cat, is_published=cat in announced, is_primary=(i == 0))
            for i, cat in enumerate(categories)
        ],
    )


def _recipients(*categories: str, **kwargs) -> tuple[list[str], list[str]]:
    to_emails, reply_to = get_recipients(_sub(*categories, **kwargs))
    return sorted(to_emails), sorted(reply_to)


# ── the flag rules ──────────────────────────────────────────────────────────

@pytest.mark.usefixtures("db_session")
def test_no_email_blocks_a_send_and_no_web_email_does_not():
    """50001 sets no_email and is gone. 50002 sets no_web_email, which this job ignores"""
    to_emails, _ = _recipients("cs.AI")
    assert to_emails == [
        "digest-cat2@example.com",
        "digest-cat@example.com",
        "noreplyto@example.com",
        "normal@example.com",
        "nowebemail@example.com",
    ]
    assert "noemail@example.com" not in to_emails


@pytest.mark.usefixtures("db_session")
def test_the_reply_to_list_follows_its_own_flag():
    """50003 is a recipient but not a Reply-To. 50001 is the other way round — the flags are
    independent, so opting out of email does not take you out of Reply-To"""
    _, reply_to = _recipients("cs.AI")
    assert reply_to == [
        "digest-cat2@example.com",
        "digest-cat@example.com",
        "noemail@example.com",
        "normal@example.com",
        "nowebemail@example.com",
    ]
    assert "noreplyto@example.com" not in reply_to


# ── the cascade reaches the right people ────────────────────────────────────

@pytest.mark.usefixtures("db_session")
def test_archive_moderators_get_it_unless_they_opted_out_of_the_category():
    """9999 mods the astro-ph archive and is in. 77777 mods it too but set no_email on
    astro-ph.HE, so the category opt-out beats their archive row"""
    to_emails, _ = _recipients("astro-ph.HE")
    assert to_emails == ["digest-archive@example.com", "no-mail-rw@example.com"]
    assert "archive-optout@example.com" not in to_emails


@pytest.mark.usefixtures("db_session")
def test_an_alias_category_moderator_is_reached_and_an_opt_out_still_holds():
    """60001 mods q-fin.EC, the alias of canonical econ.GN, and gets the mail. 60002 opted out of
    econ.GN, so their q-fin archive row must not let them back in"""
    to_emails, _ = _recipients("econ.GN")
    assert to_emails == [
        "aliascat@example.com",
        "digest-alias-archive@example.com",
        "digest-alias2@example.com",
        "digest-alias@example.com",
        "other-no-mail@example.com",
    ]
    assert "cascadeoptout@example.com" not in to_emails


@pytest.mark.usefixtures("db_session")
def test_every_category_on_the_submission_contributes():
    to_emails, _ = _recipients("cs.AI", "astro-ph.HE")
    assert to_emails == [
        "digest-archive@example.com",
        "digest-cat2@example.com",
        "digest-cat@example.com",
        "no-mail-rw@example.com",
        "noreplyto@example.com",
        "normal@example.com",
        "nowebemail@example.com",
    ]


@pytest.mark.usefixtures("db_session")
def test_a_category_outside_the_taxonomy_is_skipped_not_fatal():
    assert _recipients("cs.AI", "not.real") == _recipients("cs.AI")


@pytest.mark.usefixtures("db_session")
def test_a_submission_nobody_moderates_reaches_nobody():
    assert _recipients("hep-ex") == ([], [])

@pytest.mark.usefixtures("db_session")
def test_a_category_that_is_its_own_archive_is_reached():
    """hep-ph is one of nine active categories whose id IS an archive (gr-qc, math-ph, quant-ph
    and the rest). Their moderator rows carry no subject_class, so they land in all_archives and
    all_cats never has an entry — the archive level of the cascade is what finds them"""
    to_emails, _ = _recipients("hep-ph")
    assert to_emails == ["no-mailx234@example.com"]
# ── crosses ─────────────────────────────────────────────────────────────────

@pytest.mark.usefixtures("db_session")
def test_a_cross_only_reaches_the_categories_it_is_crossing_into():
    """the paper already sits in astro-ph.HE, so those moderators have nothing to decide"""
    to_emails, _ = _recipients(
        "astro-ph.HE", "cs.AI", sub_type="cross", announced=("astro-ph.HE",)
    )
    assert to_emails == [
        "digest-cat2@example.com",
        "digest-cat@example.com",
        "noreplyto@example.com",
        "normal@example.com",
        "nowebemail@example.com",
    ]
    assert "no-mail-rw@example.com" not in to_emails
    assert "digest-archive@example.com" not in to_emails


@pytest.mark.usefixtures("db_session")
def test_a_non_cross_reaches_every_category_it_carries():
    """the same rows as a rep, where nothing is being added and everyone still hears"""
    to_emails, _ = _recipients(
        "astro-ph.HE", "cs.AI", sub_type="rep", announced=("astro-ph.HE",)
    )
    assert "digest-archive@example.com" in to_emails
    assert "normal@example.com" in to_emails



