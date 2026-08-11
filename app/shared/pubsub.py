"""pubsub message pulling, shared by the jobs that read from a subscription"""
import logging
import time
from typing import List

from google.pubsub import ReceivedMessage, SubscriberClient

from app.shared.config import settings

logger = logging.getLogger(__name__)


def get_messages(subscriber: SubscriberClient, sub_path:str) -> List[ReceivedMessage]:
    """get a large batch of messages from the pubsub topic"""

    collected_msgs: List[ReceivedMessage] = []
    start_time = time.time()

    while ( #loop to try to collect large batch of messages
        len(collected_msgs)< settings.PUBSUB_BATCH_SIZE #stop if enough messages are found
        and time.time() -start_time < settings.PUBSUB_MAX_PULL_SEC #stop if we have been waiting too long
        ):

        #keep trying to acquire messages
        response = subscriber.pull(
            request={
                "subscription": sub_path,
                "max_messages": settings.PUBSUB_BATCH_SIZE,
            }
        )
        if not response.received_messages:
            logger.debug("Stopped pulling due to no messages recieved")
            break #stop loop if there are no more messages

        collected_msgs.extend(response.received_messages)

    return collected_msgs
