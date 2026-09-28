"""tests for reading a snapshot message into the shape the job works on

"""
import base64
import json
import logging
from datetime import datetime, timezone
from unittest.mock import patch

import pytest
from cloudevents.http import CloudEvent
from pydantic import ValidationError

from app.new_subs.main import NewSubParams, _build_submission, handle_new_submission
from app.shared.submission import SubmissionBase, SubmissionCat

SUB_ID = 7850001
USER_ID = 246234


def _message(**overrides) -> dict:
    """one snapshot message. keyword args replace fields of arXiv_submissions"""
    submission = {
        "submission_id": SUB_ID,
        "status": 4,
        "type": "new",
        "auto_hold": 0,
        "title": "A Submission For A Test",
        "authors": "Pippin Otter, Waffles Hamster",
        "submitter_name": "Pippin Otter",
        "submitter_id": USER_ID,
        "submit_time": "2026-09-23T20:40:10",
    }
    submission.update(overrides)
    return {
        "arXiv_submissions": submission,
        "arXiv_submission_category": [
            {"submission_id": SUB_ID, "category": "econ.EM", "is_primary": 1, "is_published": 0},
        ],
        # a real message carries several more keys we dont use
        "bonus_key": "ignored",
    }


def _cloud_event(payload) -> CloudEvent:
    """the message as Eventarc delivers it"""
    return CloudEvent(
        {
            "type": "google.cloud.pubsub.topic.v1.messagePublished",
            "source": "//pubsub.googleapis.com/projects/arxiv-development/topics/submit-info",
        },
        {"message": {"data": base64.b64encode(json.dumps(payload).encode()).decode()}},
    )


def _built(**overrides) -> SubmissionBase:
    return _build_submission(NewSubParams.model_validate(_message(**overrides)))


# ── the whole conversion ────────────────────────────────────────────────────

def test_a_message_becomes_a_submission():
    assert _built() == SubmissionBase(
        submission_id=7850001,
        title="A Submission For A Test",
        authors="Pippin Otter, Waffles Hamster",
        status=4,
        submitter_name="Pippin Otter",
        submitter_id=246234,
        submit_time=datetime(2026, 9, 23, 20, 40, 10, tzinfo=timezone.utc),
        sub_type="new",
        auto_hold=False,
        categories=[SubmissionCat(category="econ.EM", is_published=False, is_primary=True)],
    )


# ── what gets dropped ───────────────────────────────────────────────────────

def test_the_rest_of_the_snapshot_is_dropped():
    """the publisher sends urls, checksums, classifier data and more — bonus_key here"""
    params = NewSubParams.model_validate(_message())
    assert set(params.model_dump()) == {"arXiv_submissions", "arXiv_submission_category"}


# ── submit_time ─────────────────────────────────────────────────────────────

def test_a_time_with_no_offset_is_read_as_utc():
    """the column is naive UTC, so isoformat() sends no offset"""
    assert _built(submit_time="2026-09-23T20:40:10").submit_time == datetime(
        2026, 9, 23, 20, 40, 10, tzinfo=timezone.utc
    )


def test_a_time_with_an_offset_keeps_it():
    assert _built(submit_time="2026-09-23T20:40:10+02:00").submit_time == datetime(
        2026, 9, 23, 18, 40, 10, tzinfo=timezone.utc
    )


# ── nullable columns ────────────────────────────────────────────────────────

def test_null_columns_become_their_empty_values():
    """every one of these is nullable, and the rest of the job expects a real value"""
    sub = _built(title=None, authors=None, submitter_name=None, submitter_id=None,
                 type=None, auto_hold=None)
    assert (sub.title, sub.authors, sub.submitter_name) == ("", "", "")
    assert (sub.submitter_id, sub.sub_type, sub.auto_hold) == (0, "", False)


def test_auto_hold_is_read_as_a_bool():
    assert _built(auto_hold=1).auto_hold is True


# ── what a message must carry ───────────────────────────────────────────────

def test_a_message_without_the_submission_is_rejected():
    payload = _message()
    del payload["arXiv_submissions"]
    with pytest.raises(ValidationError):
        NewSubParams.model_validate(payload)


def test_a_message_without_the_category_key_is_rejected():
    payload = _message()
    del payload["arXiv_submission_category"]
    with pytest.raises(ValidationError):
        NewSubParams.model_validate(payload)


def test_a_submission_with_no_categories_is_allowed():
    """the key has to be there; an empty list is a real state"""
    payload = _message()
    payload["arXiv_submission_category"] = []
    assert _build_submission(NewSubParams.model_validate(payload)).categories == []


def test_a_message_without_a_status_is_rejected():
    """status is the one NOT NULL column of the set"""
    payload = _message()
    del payload["arXiv_submissions"]["status"]
    with pytest.raises(ValidationError):
        NewSubParams.model_validate(payload)


# ── the handler ─────────────────────────────────────────────────────────────

def test_a_good_message_is_processed():
    with patch("app.new_subs.main.SCOUT_ONLY", False), \
         patch("app.new_subs.main.process_new_submission") as process:
        handle_new_submission(_cloud_event(_message()))
    process.assert_called_once()
    assert process.call_args.args[0].submission_id == SUB_ID


def test_an_unparseable_payload_is_acked_not_processed():
    """returning acks it. redelivery would not make it parse"""
    event = CloudEvent(
        {"type": "google.cloud.pubsub.topic.v1.messagePublished", "source": "//pubsub/x"},
        {"message": {"data": base64.b64encode(b"not json").decode()}},
    )
    with patch("app.new_subs.main.process_new_submission") as process:
        handle_new_submission(event)
    process.assert_not_called()


def test_a_payload_of_the_wrong_shape_is_acked_not_processed():
    with patch("app.new_subs.main.process_new_submission") as process:
        handle_new_submission(_cloud_event({"submission_id": SUB_ID}))
    process.assert_not_called()


def test_a_processing_failure_is_left_for_redelivery():
    """anything raised out of the handler leaves the message unacked"""
    with patch("app.new_subs.main.SCOUT_ONLY", False), \
         patch("app.new_subs.main.process_new_submission", side_effect=RuntimeError("boom")):
        with pytest.raises(RuntimeError):
            handle_new_submission(_cloud_event(_message()))


