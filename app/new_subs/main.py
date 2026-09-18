"""entrypoint for the new_subs job: emails moderators about new submissions

A Pub/Sub **push** subscription delivers one message here per new submission — this job runs
as a Cloud Run service. Returning acks the message; raising
leaves it unacked and Pub/Sub redelivers.
"""
import base64
import json
import logging
import functions_framework
from cloudevents.http import CloudEvent
from pydantic import BaseModel

from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok

from app.new_subs.process import process_new_submission

# do onetime setup for the container before start serving
setup_logging()
logger = logging.getLogger(__name__)

if not email_config_ok():
    raise RuntimeError("email configuration is invalid — refusing to start")


class NewSubParams(BaseModel):
    """one new-submission message
    """
    submission_id: int
    #TODO confirm whats in payload


#handle individual submissions
@functions_framework.cloud_event
def handle_new_submission(cloud_event: CloudEvent) -> None:
    """one message, one submission"""

    try:
        payload = json.loads(base64.b64decode(cloud_event.data["message"]["data"]))
        submission_id = NewSubParams.model_validate(payload).submission_id
    except Exception:
        logger.exception(f"[PARSE FAILURE] data: {cloud_event.data}")
        return  # ack — redelivery will not make it parse

    
    process_new_submission(submission_id)
