"""entrypoint for the new_subs job: emails moderators about new submissions"""
import base64
import json
import logging
from datetime import datetime
from typing import Optional

import functions_framework
from cloudevents.http import CloudEvent
from pydantic import BaseModel, Field

from app.shared.submission import SubmissionCat, as_utc
from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok

from app.new_subs.process import process_new_submission
from app.new_subs.submission import NewSubmission

#SCOUTING: log every message in full, ack it, and send nothing. 
SCOUT_ONLY = True
SCOUT_CHUNK_CHARS = 90_000

# do onetime setup for the container before start serving
setup_logging()
logger = logging.getLogger(__name__)

if not email_config_ok():
    raise RuntimeError("email configuration is invalid — refusing to start")


class MessageSubmission(BaseModel):
    """the arXiv_submissions row. drops unused data from published message.
    """
    submission_id: int
    status: int 
    auto_hold: Optional[bool] = None
    type: Optional[str] = None #submission type
    title: Optional[str] = None
    authors: Optional[str] = None
    submitter_name: Optional[str] = None
    submitter_id: Optional[int] = None
    submit_time: Optional[datetime] = None
    comments: Optional[str] = None
    journal_ref: Optional[str] = None
    doi: Optional[str] = None
    abstract: Optional[str] = None


class NewSubParams(BaseModel):
    #the shape of the incoming message payload
    arXiv_submissions: MessageSubmission
    arXiv_submission_category: list[SubmissionCat]
    arXiv_submission_abs_classifier_data: dict = Field(default_factory=dict)


def _build_submission(params: NewSubParams) -> NewSubmission:
    """the message as the object the rest of the job works on"""
    sub = params.arXiv_submissions
    return NewSubmission(
        submission_id=sub.submission_id,
        title=sub.title or "",
        authors=sub.authors or "",
        status=sub.status,
        submitter_name=sub.submitter_name or "",
        submitter_id=sub.submitter_id or 0,
        #the column is naive UTC, so its isoformat() arrives without an offset
        submit_time=as_utc(sub.submit_time),
        categories=list(params.arXiv_submission_category),
        sub_type=sub.type or "",
        auto_hold=bool(sub.auto_hold),
        comments=sub.comments,
        journal_ref=sub.journal_ref,
        doi=sub.doi,
        abstract=sub.abstract,
        system_proposed_primary=params.arXiv_submission_abs_classifier_data.get("autoproposal_primary"),
    )


def _log_whole_payload(payload) -> None:
    """the entire message, split to stay under the Cloud Logging entry size cap"""
    text = json.dumps(payload, indent=2, sort_keys=True, default=str)
    parts = [text[i:i + SCOUT_CHUNK_CHARS] for i in range(0, len(text), SCOUT_CHUNK_CHARS)]
    logger.info(f"[SCOUT] payload is {len(text)} chars, top-level keys {sorted(payload)}")
    for number, part in enumerate(parts, start=1):
        logger.info(f"[SCOUT] payload part {number}/{len(parts)}\n{part}")


#handle individual submissions
@functions_framework.cloud_event
def handle_new_submission(cloud_event: CloudEvent) -> None:
    """one message, one submission"""

    #read the pubsub data
    try:
        payload = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
    except Exception:
        logger.exception(f"Could not decode message, envelope: {cloud_event.data}")
        return

    if SCOUT_ONLY:
        _log_whole_payload(payload)

    try:
        params = NewSubParams.model_validate(payload)
    except Exception:
        logger.exception(f"Payload did not match NewSubParams. top-level keys: {list(payload)}")
        logger.error(f"Full payload: {json.dumps(payload, default=str)}")
        return

    if SCOUT_ONLY:
        logger.info(f"[SCOUT] parses cleanly: {_build_submission(params)}")
        return #ack without sending anything

    process_new_submission(_build_submission(params))
