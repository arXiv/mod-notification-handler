"""tests for shared formatting helpers"""
from app.shared.utils.formatting import (
    MAX_AUTHORS,
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
