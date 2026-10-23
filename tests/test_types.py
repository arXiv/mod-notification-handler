"""the type checker, run as a test so it runs with the rest of the suite. scope is [tool.mypy] in pyproject.toml"""
from mypy import api


def test_app_type_checks():
    stdout, stderr, exit_status = api.run([])
    #if a mypy update rewords its success message, this string may need to change
    assert stdout.startswith("Success: no issues found in ")
    assert (stderr, exit_status) == ("", 0)
