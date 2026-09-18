"""entrypoint for the new_subs job: emails moderators about new submissions

A Pub/Sub **push** subscription delivers one message here per new submission — this job runs
as a Cloud Run service. Returning acks the message; raising
leaves it unacked and Pub/Sub redelivers.
"""
import base64
import json
import logging
from datetime import datetime
from typing import Optional

import functions_framework
from cloudevents.http import CloudEvent
from pydantic import BaseModel

from app.shared.submission import SubmissionBase, SubmissionCat, as_utc
from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok

from app.new_subs.process import process_new_submission

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


class NewSubParams(BaseModel):
    #the shape of the incoming message payload
    arXiv_submissions: MessageSubmission
    arXiv_submission_category: list[SubmissionCat]


def _build_submission(params: NewSubParams) -> SubmissionBase:
    """the message as the object the rest of the job works on"""
    sub = params.arXiv_submissions
    return SubmissionBase(
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
    )


#handle individual submissions
@functions_framework.cloud_event
def handle_new_submission(cloud_event: CloudEvent) -> None:
    """one message, one submission"""

    #read the pubsub data
    try:
        payload = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
        params = NewSubParams.model_validate(payload)
    except Exception:
        logger.exception(f"[PARSE FAILURE] data: {cloud_event.data}")
        return  # ack — redelivery will not make it parse

    process_new_submission(_build_submission(params))
