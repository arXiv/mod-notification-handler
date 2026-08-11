"""tests that mod_actions' main() bails out before touching pubsub on bad email config

email_config_ok() reads settings inside app.shared.utils.startup, so that is the patch target
"""
from unittest.mock import patch

from app.mod_actions.main import main


def test_main_exits_if_redirect_recipient_missing():
    with patch("app.shared.utils.startup.settings") as mock_settings, \
         patch("app.mod_actions.main.pubsub_v1.SubscriberClient") as mock_client:
        mock_settings.SEND_EMAILS = True
        mock_settings.REDIRECT_EMAILS = True
        mock_settings.REDIRECT_RECIPIENT = None
        main()
        mock_client.assert_not_called()


def test_main_exits_if_no_redirect_outside_production():
    with patch("app.shared.utils.startup.settings") as mock_settings, \
         patch("app.mod_actions.main.pubsub_v1.SubscriberClient") as mock_client:
        mock_settings.SEND_EMAILS = True
        mock_settings.REDIRECT_EMAILS = False
        mock_settings.ENV = "LOCAL"
        main()
        mock_client.assert_not_called()
