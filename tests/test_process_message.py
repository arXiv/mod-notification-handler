import json
import pytest
from datetime import datetime, timezone
from types import SimpleNamespace

from app.process import process_messages, _parse_message
from app.schema import  CommentData, PromoteData, NewPropData, PropRespData



def _make_pubsub_message(ack_id: str, payload: dict, publish_time: datetime):
    "helper function to model what pubsub messages look like"
    return SimpleNamespace(
        ack_id=ack_id,
        message=SimpleNamespace(
            data=json.dumps(payload).encode("utf-8"),  
            publish_time=publish_time,
            attributes={}
        )
    )


def test_collect_acks():
    msg1 = _make_pubsub_message(
        "ack-1",
        {"submission_id": 123, "action": "created"},
        datetime(2024, 1, 1, 10, 0),
    )
    msg2 = _make_pubsub_message(
        "ack-2",
        {"submission_id": 123, "action": "created"},
        datetime(2024, 1, 1, 10, 0),
    )

    messages = [msg1, msg2]
    result = process_messages(messages) #type: ignore 
    assert result == ["ack-1", "ack-2"]

def test_general_parse():
    good_comment = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Comment Added",
        "data": {"comment": "hello"}
    }

    bad1 = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Cartwheel",
        "data": {"comment": "goodbye"}
    }

    bad2 = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": "cs.LG",
        "action": "Comment Added",
        "data": {"comment": "goodbye"}
    }

    with pytest.raises(Exception):
        full_note, simple_note = _parse_message(bad1)

    with pytest.raises(Exception):
        full_note, simple_note = _parse_message(bad2)

    full_note, simple_note=_parse_message(good_comment)
    assert full_note.action== "Comment Added"
    assert full_note.categories== ["cs.LG", "cs.AI"]
    assert full_note.submission_id== 123
    assert full_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)


def test_parse_comment():
    good_comment = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Comment Added",
        "data": {"comment": "hello"}
    }

    bad_comment = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Comment Added",
        "data": {"comment": 5}
    }

    with pytest.raises(Exception):
        full_note, simple_note = _parse_message(bad_comment)

    full_note, simple_note=_parse_message(good_comment)
    assert full_note.action== "Comment Added"
    assert full_note.categories== ["cs.LG", "cs.AI"]
    assert full_note.submission_id== 123
    assert isinstance(simple_note.data, CommentData)
    assert simple_note.data.comment=="hello"
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_parse_new_prop():
    good_new_prop = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "New Category Proposal",
        "data": {"msg": "new category request"}
    }

    bad_new_prop = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "New Category Proposal",
        "data": {"message": "new category request"} 
    }

    with pytest.raises(Exception):
        _parse_message(bad_new_prop)

    full_note, simple_note = _parse_message(good_new_prop)

    assert full_note.action == "New Category Proposal"
    assert full_note.categories == ["cs.LG", "cs.AI"]
    assert full_note.submission_id == 123

    assert isinstance(simple_note.data, NewPropData)
    assert simple_note.data.msg == "new category request"
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_parse_promote():
    good_promote = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Category Promotion",
        "data": {
            "category": "cs.LG",
            "promotion_type": "primary",
            "category_change": "promoted"
        }
    }

    bad_promote = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Category Promotion",
        "data": {
            "category": "cs.LG",
            "promotion_type": "invalid",  # bad enum
            "category_change": "promoted"
        }
    }

    with pytest.raises(Exception):
        _parse_message(bad_promote)

    full_note, simple_note = _parse_message(good_promote)

    assert full_note.action == "Category Promotion"
    assert full_note.categories == ["cs.LG", "cs.AI"]
    assert full_note.submission_id == 123

    assert isinstance(simple_note.data, PromoteData)
    assert simple_note.data.category == "cs.LG"
    assert simple_note.data.promotion_type == "primary"
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_parse_prop_response():
    good_prop_resp = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Category Proposal Responses",
        "data": {
            "responses": "accepted",
            "category_change": "none"
        }
    }

    bad_prop_resp = {
        "time": "2024-01-01T10:00:00Z",
        "submission_id": 123,
        "user_id": 1,
        "categories": ["cs.LG", "cs.AI"],
        "action": "Category Proposal Responses",
        "data": {
            "responses": 123,  # invalid type
            "category_change": "none"
        }
    }

    with pytest.raises(Exception):
        _parse_message(bad_prop_resp)

    full_note, simple_note = _parse_message(good_prop_resp)

    assert full_note.action == "Category Proposal Responses"
    assert full_note.categories == ["cs.LG", "cs.AI"]
    assert full_note.submission_id == 123
    assert full_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

    assert isinstance(simple_note.data, PropRespData)
    assert simple_note.data.responses == "accepted"
    assert simple_note.data.category_change == "none"
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)



