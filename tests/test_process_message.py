import json
from unittest.mock import patch, Mock
import pytest
from datetime import datetime, timezone
from types import SimpleNamespace

from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.process import process_messages, _parse_message, _convert_messages, _build_email_tasks
from app.schema import  CommentData, PromoteData, NewPropData, PropRespData, ConsolidatedNotifications, SimplifiedNotification

GOOD_COMMENT = {
    "time": "2024-01-01T10:00:00Z",
    "submission_id": 123,
    "user_id": 1,
    "categories": ["cs.LG", "cs.AI"],
    "action": "Comment Added",
    "data": {"comment": "hello"}
}

GOOD_PROMOTE = {
    "time": "2024-01-01T10:00:00Z",
    "submission_id": 124,
    "user_id": 1,
    "categories": ["cs.LG", "cs.AI"],
    "action": "Category Promotion",
    "data": {
        "category": "cs.LG",
        "promotion_type": "primary",
        "category_change": "promoted"
    }
}

BAD_PROMOTE = {
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

GOOD_PROP_RESP = {
    "time": "2024-01-01T10:00:00Z",
    "submission_id": 123,
    "user_id": 2,
    "categories": ["hep-lat"],
    "action": "Category Proposal Responses",
    "data": {
        "responses": "Primary accepted: hep-lat",
        "category_change": "no primary -> hep-lat"
    }
}

def _make_pubsub_message(ack_id: str, payload: dict):
    "helper function to model what pubsub messages look like"
    return SimpleNamespace(
        ack_id=ack_id,
        message=SimpleNamespace(
            data=json.dumps(payload).encode("utf-8"),  
            attributes={}
        )
    )


def test_collect_acks():
    msg1 = _make_pubsub_message(
        "ack-1",
        {"submission_id": 123, "action": "created"},
    )
    msg2 = _make_pubsub_message(
        "ack-2",
        {"submission_id": 123, "action": "created"},
    )

    messages = [msg1, msg2]
    result = process_messages(messages) #type: ignore 
    assert result == ["ack-1", "ack-2"]

def test_general_parse():

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

    full_note, simple_note=_parse_message(GOOD_COMMENT)
    assert full_note.action== "Comment Added"
    assert full_note.categories== ["cs.LG", "cs.AI"]
    assert full_note.submission_id== 123
    assert full_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_parse_comment():
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

    full_note, simple_note=_parse_message(GOOD_COMMENT)
    assert full_note.action== "Comment Added"
    assert full_note.categories== ["cs.LG", "cs.AI"]
    assert full_note.submission_id== 123
    assert isinstance(simple_note.data, CommentData)
    assert simple_note.data.comment=="hello"
    assert simple_note.user_id == 1
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
    with pytest.raises(Exception):
        _parse_message(BAD_PROMOTE)

    full_note, simple_note = _parse_message(GOOD_PROMOTE)

    assert full_note.action == "Category Promotion"
    assert full_note.categories == ["cs.LG", "cs.AI"]
    assert full_note.submission_id == 124

    assert isinstance(simple_note.data, PromoteData)
    assert simple_note.data.category == "cs.LG"
    assert simple_note.data.promotion_type == "primary"
    assert simple_note.user_id == 1
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_parse_prop_response():

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

    full_note, simple_note = _parse_message(GOOD_PROP_RESP)

    assert full_note.action == "Category Proposal Responses"
    assert full_note.categories == ["hep-lat"]
    assert full_note.submission_id == 123
    assert full_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

    assert isinstance(simple_note.data, PropRespData)
    assert simple_note.data.responses == "Primary accepted: hep-lat"
    assert simple_note.data.category_change == "no primary -> hep-lat"
    assert simple_note.time == datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)

def test_consolidate_messages():

    msg1 = _make_pubsub_message("ack-1", GOOD_COMMENT)
    msg2 = _make_pubsub_message("ack-3", GOOD_COMMENT)
    msg3 = _make_pubsub_message("ack-4", GOOD_PROMOTE)
    msg4 = _make_pubsub_message("ack-5", BAD_PROMOTE)
    msg5 = _make_pubsub_message("ack-7", GOOD_PROP_RESP)
    messages=[msg1, msg2, msg3, msg4, msg5]

    data, ids = _convert_messages(messages) #type: ignore

    assert ids == ['ack-5'] #only parse failures returned; valid acks live on each submission

    sub2=data[124]
    assert sub2.ack_ids == ['ack-4']
    assert sub2.categories== {CATEGORIES_ACTIVE['cs.LG'], CATEGORIES_ACTIVE['cs.AI']} #type: ignore
    assert sub2.user_ids== {1}
    assert len(sub2.changes) == 1
    assert sub2.changes[0].time== datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    assert isinstance(sub2.changes[0].data, PromoteData)
    assert sub2.changes[0].data.category == 'cs.LG'
    assert sub2.changes[0].data.category_change == "promoted"
    assert sub2.changes[0].data.promotion_type == "primary"

    sub1=data[123]
    assert sub1.ack_ids == ['ack-1', 'ack-3', 'ack-7']
    assert sub1.categories== {CATEGORIES_ACTIVE['cs.LG'], CATEGORIES_ACTIVE['cs.AI'], CATEGORIES_ACTIVE['hep-lat']} #type: ignore
    assert sub1.user_ids== {1, 2}
    assert len(sub1.changes) == 3
    #comment1
    assert sub1.changes[0].time== datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    assert isinstance(sub1.changes[0].data, CommentData)
    assert sub1.changes[0].data.comment == 'hello'
    #comment2
    assert sub1.changes[1].time== datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    assert isinstance(sub1.changes[1].data, CommentData)
    assert sub1.changes[1].data.comment == 'hello'
    #proposal resp
    assert sub1.changes[2].time== datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    assert isinstance(sub1.changes[2].data, PropRespData)
    assert sub1.changes[2].data.category_change == 'no primary -> hep-lat'
    assert sub1.changes[2].data.responses=="Primary accepted: hep-lat"

_NOTE = SimplifiedNotification(
    time=datetime(2024, 1, 1, tzinfo=timezone.utc),
    user_id=246231,
    data=CommentData(comment="test"),
)
_NOTE_2 = SimplifiedNotification(
    time=datetime(2024, 1, 2, tzinfo=timezone.utc),
    user_id=681201,
    data=CommentData(comment="test reply"),
)

@pytest.mark.usefixtures("db_session")
def test_sole_actor_excluded():
    notifications = ConsolidatedNotifications(
        submission_id=1,
        categories={CATEGORIES_ACTIVE['q-bio.NC']},
        user_ids={246231},
        changes=[_NOTE],
    )
    tasks, _ = _build_email_tasks({1: notifications})
    assert len(tasks) == 1
    task = tasks[0]
    assert 'no-mail@example.com' not in task.to_emails          # sole actor excluded from email
    assert 'also-dont-mail@example.com' in task.to_emails       # uninvolved mod still gets email
    assert 'no-mail@example.com' in (task.reply_to_emails or []) # exclusion doesn't affect reply-to

@pytest.mark.usefixtures("db_session")
def test_multi_actor_not_excluded():
    notifications = ConsolidatedNotifications(
        submission_id=1,
        categories={CATEGORIES_ACTIVE['q-bio.NC']},
        user_ids={246231, 681201},
        changes=[_NOTE, _NOTE_2],
    )
    tasks, _ = _build_email_tasks({1: notifications})
    assert len(tasks) == 1
    task = tasks[0]
    assert 'no-mail@example.com' in task.to_emails          # 246231 not excluded (multiple actors)
    assert 'also-dont-mail@example.com' in task.to_emails   # 681201 not excluded
    assert 'dont-mail@example.com' in task.to_emails        # uninvolved mod 1234544 gets email

@pytest.mark.usefixtures("db_session")
def test_skip_task_with_no_recipients():
    notifications = ConsolidatedNotifications(
        submission_id=1,
        categories={CATEGORIES_ACTIVE['econ.EM']},
        user_ids={99999},
        changes=[_NOTE],
    )
    tasks, _ = _build_email_tasks({1: notifications})
    assert tasks == []

@pytest.mark.usefixtures("db_session")
def test_send_error_does_not_abort():
    msg1 = _make_pubsub_message("ack-1", GOOD_COMMENT)   # sub 123, cs.AI + cs.LG
    msg2 = _make_pubsub_message("ack-2", GOOD_PROMOTE)   # sub 124, cs.AI + cs.LG

    mock_send = Mock(side_effect=[RuntimeError("smtp down"), None])
    with patch("app.process.send_email", mock_send):
        ack_ids = process_messages([msg1, msg2])

    assert "ack-1" not in ack_ids  # failed send — sub 123 will redeliver
    assert "ack-2" in ack_ids      # successful send — sub 124 acked
    assert mock_send.call_count == 2

@pytest.mark.usefixtures("db_session")
def test_all_successful_sends_all_acked():
    msg1 = _make_pubsub_message("ack-1", GOOD_COMMENT)  # sub 123
    msg2 = _make_pubsub_message("ack-2", GOOD_PROMOTE)  # sub 124
    msg3 = _make_pubsub_message("ack-3", BAD_PROMOTE)   # parse failure

    with patch("app.process.send_email"):
        ack_ids = process_messages([msg1, msg2, msg3])

    assert "ack-1" in ack_ids  # successful send
    assert "ack-2" in ack_ids  # successful send
    assert "ack-3" in ack_ids  # parse failure — acked immediately, won't retry
