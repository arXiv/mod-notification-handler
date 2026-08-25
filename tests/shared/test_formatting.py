"""tests for shared formatting helpers"""
from app.shared.utils.formatting import (
    MAX_AUTHORS,
    build_category_string,
    split_categories,
    truncate_authors,
)


# ── build_category_string ───────────────────────────────────────────────────

def test_category_string_empty():
    assert build_category_string([]) == "-"


def test_category_string_primary_only():
    assert build_category_string([("cs.LG", 1)]) == "cs.LG"


def test_category_string_primary_and_cross():
    # math.ST is canonical target of stat.TH alias → stat.TH also added
    result = build_category_string([("cs.LG", 1), ("cs.AI", 0), ("math.ST", 0)])
    assert result == "cs.LG cs.AI math.ST stat.TH"


def test_category_string_no_primary_with_secondaries():
    result = build_category_string([("cs.AI", 0), ("cs.LG", 0)])
    assert result == "- cs.AI cs.LG"


def test_category_string_alias_expansion():
    # math-ph is canonical target of math.MP alias → math.MP added to secondaries
    result = build_category_string([("cs.LG", 0), ("math-ph", 1)])
    assert result == "math-ph cs.LG math.MP"


# ── split_categories ────────────────────────────────────────────────────────

def test_split_categories_empty():
    assert split_categories([]) == (None, [])


def test_split_categories_primary_is_not_in_secondaries():
    primary, secondaries = split_categories([("cs.LG", 1), ("cs.AI", 0)])
    assert primary == "cs.LG"
    assert secondaries == ["cs.AI"]


def test_split_categories_no_primary_returns_none():
    primary, secondaries = split_categories([("cs.AI", 0)])
    assert primary is None
    assert secondaries == ["cs.AI"]


def test_split_categories_secondaries_are_sorted():
    _, secondaries = split_categories([("cs.LG", 1), ("stat.ML", 0), ("astro-ph.CO", 0)])
    assert secondaries == ["astro-ph.CO", "stat.ML"]

def test_canonical_primary_gains_its_alias():
    primary, secondaries = split_categories([("math-ph", 1)])
    assert primary == "math-ph"
    assert secondaries == ["math.MP"]

def test_canonical_secondary_gains_its_alias():
    _, secondaries = split_categories([("cs.LG", 1), ("econ.GN", 0)])
    assert secondaries == ["econ.GN", "q-fin.EC"]



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
