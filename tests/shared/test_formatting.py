"""tests for shared formatting helpers"""
from app.shared.utils.formatting import build_category_string


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
