"""manages the job and pubsub message handling"""

import logging
import time
from typing import List

from google.cloud import pubsub_v1
from google.pubsub import ReceivedMessage, SubscriberClient

from app.config import settings
from app.process import process_messages


logging.basicConfig(level=settings.LOG_LEVEL)
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


def main():

    #fail fast on email misconfiguration before touching the queue
    if settings.SEND_EMAILS:
        if settings.REDIRECT_EMAILS and not settings.REDIRECT_RECIPIENT:
            logger.error("SEND_EMAILS=True and REDIRECT_EMAILS=True but REDIRECT_RECIPIENT is not set — exiting")
            return
        if not settings.REDIRECT_EMAILS and settings.ENV != "PRODUCTION":
            logger.error("SEND_EMAILS=True and REDIRECT_EMAILS=False but ENV is not PRODUCTION — exiting")
            return
    elif settings.ENV == "PRODUCTION":
        logger.warning("SEND_EMAILS=False in PRODUCTION — messages will be acked without sending email")

    #get messages
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(settings.GCP_PROJECT_ID, settings.PUBSUB_SUBSCRIPTION_ID)
    messages=get_messages(subscriber, subscription_path)
    if len(messages)==0:
        logger.warning("No messages found.")
        return

    def ack(ids: list[str]) -> None:
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ids})

    process_messages(messages, ack_fn=ack)


if __name__ == "__main__":
    main()