from unittest.mock import MagicMock

from app.main import get_messages

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