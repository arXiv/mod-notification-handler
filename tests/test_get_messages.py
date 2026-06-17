from unittest.mock import MagicMock, patch

from app.main import get_messages, main

class FakeResponse:
    def __init__(self, messages):
        self.received_messages = messages


def test_get_messages_collects_multiple_batches():
    subscriber = MagicMock()

    # simulate two pulls
    subscriber.pull.side_effect = [
        FakeResponse(["msg1", "msg2"]),
        FakeResponse(["msg3"]),
        FakeResponse([]),  # stop condition
    ]

    result = get_messages(subscriber, "fake-sub")

    assert result == ["msg1", "msg2", "msg3"]
    assert subscriber.pull.call_count == 3

def test_get_messages_stops_on_empty():
    subscriber = MagicMock()
    subscriber.pull.return_value = FakeResponse([])

    result = get_messages(subscriber, "fake-sub")

    assert result == []
    subscriber.pull.assert_called_once()


def test_main_exits_if_redirect_recipient_missing():
    with patch("app.main.settings") as mock_settings, \
         patch("app.main.pubsub_v1.SubscriberClient") as mock_client:
        mock_settings.SEND_EMAILS = True
        mock_settings.REDIRECT_EMAILS = True
        mock_settings.REDIRECT_RECIPIENT = None
        main()
        mock_client.assert_not_called()


def test_main_exits_if_no_redirect_outside_production():
    with patch("app.main.settings") as mock_settings, \
         patch("app.main.pubsub_v1.SubscriberClient") as mock_client:
        mock_settings.SEND_EMAILS = True
        mock_settings.REDIRECT_EMAILS = False
        mock_settings.ENV = "LOCAL"
        main()
        mock_client.assert_not_called()