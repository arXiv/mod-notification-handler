"""tests for shared formatting helpers"""
from datetime import datetime, timezone

import pytest

from app.shared.utils.formatting import (
    ET,
    MAX_AUTHORS,
    fmt_time,
    now_et,
    truncate_authors,
)



# ── truncate_authors ─────────────────────────────────────────────

def test_truncate_authors_keeps_the_first_seven_names():
    authors = ", ".join(f"Author {i}" for i in range(12))
    assert truncate_authors(authors) == (
        "Author 0, Author 1, Author 2, Author 3, Author 4, Author 5, Author 6, ..."
    )

def test_truncate_authors_under_limit():
    authors = ", ".join(f"Author {i}" for i in range(6))
    assert truncate_authors(authors) == authors


def test_truncate_authors_at_limit():
    authors = ", ".join(f"Author {i}" for i in range(7))
    assert truncate_authors(authors) == authors
    assert "..." not in truncate_authors(authors)


def test_truncate_authors_one_over_limit():
    authors = ", ".join(f"Author {i}" for i in range(8))
    assert truncate_authors(authors) == (
        "Author 0, Author 1, Author 2, Author 3, Author 4, Author 5, Author 6, ..."
    )
    assert "Author 7" not in truncate_authors(authors)


def test_truncate_authors_normalises_whitespace():
    assert truncate_authors("A ,  B , C") == "A, B, C"


def test_an_aware_time_is_converted_to_east_coast():
    assert fmt_time(datetime(2026, 7, 27, 19, 0, tzinfo=timezone.utc)) == "07-27 15:00 EDT"


def test_a_naive_time_is_assumed_utc_and_warned_about(caplog):
    #assuming utc keeps the output the same everywhere. the warning is there because assuming
    #is not knowing — whoever read the value should have attached its zone
    with caplog.at_level("WARNING"):
        assert fmt_time(datetime(2026, 7, 27, 19, 0)) == "07-27 15:00 EDT"
    assert "assuming UTC" in caplog.text


# ── now_et ──────────────────────────────────────────────────────────────────

def test_now_et_is_arxiv_business_time():
    assert str(ET) == "America/New_York"
    assert now_et().tzinfo is ET


def test_now_et_is_not_the_utc_date_late_in_the_evening():
    #the case that makes this matter: after 20:00 ET the UTC date has already rolled over
    late_evening_et = datetime(2026, 7, 28, 2, 0, tzinfo=timezone.utc).astimezone(ET)
    assert late_evening_et.date().isoformat() == "2026-07-27"
    assert late_evening_et.hour == 22
