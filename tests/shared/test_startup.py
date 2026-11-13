"""email_config_ok() reads settings inside app.shared.utils.startup, so that is the patch target"""
from unittest.mock import patch

import pytest

from app.shared.utils.startup import email_config_ok


def _settings(mock_settings, halon_creds):
    mock_settings.SEND_EMAILS = True
    mock_settings.REDIRECT_EMAILS = True
    mock_settings.REDIRECT_RECIPIENT = "redirect@example.com"
    mock_settings.HALON_CREDS = halon_creds


@pytest.mark.parametrize("halon_creds", [
    "smtps://user:pass@relay.example.com:465",
    "smtps://user:pass@relay.example.com",
])
def test_good_halon_creds_pass(halon_creds):
    with patch("app.shared.utils.startup.settings") as mock_settings:
        _settings(mock_settings, halon_creds)
        assert email_config_ok() is True


@pytest.mark.parametrize("halon_creds", [
    "smtps://user:pass@host:port",
    "smtps://user@relay.example.com:465",
    "smtps://relay.example.com:465",
    "smtps://:pass@relay.example.com:465",
    "smtps://user:@relay.example.com:465",
    "",
])
def test_bad_halon_creds_fail(halon_creds):
    with patch("app.shared.utils.startup.settings") as mock_settings:
        _settings(mock_settings, halon_creds)
        assert email_config_ok() is False


def test_halon_creds_are_not_checked_when_sending_is_off():
    with patch("app.shared.utils.startup.settings") as mock_settings:
        _settings(mock_settings, "not a url")
        mock_settings.SEND_EMAILS = False
        mock_settings.ENV = "LOCAL"
        assert email_config_ok() is True
