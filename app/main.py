"""manages the job and pubsub message handling"""

import logging
import time
from typing import List

from google.cloud import pubsub_v1
from google.pubsub import ReceivedMessage, SubscriberClient

from app.process import process_messages
from app.moderators import get_all_moderators

PROJECT_ID = "arxiv-development"
SUBSCRIPTION_ID = "mod-notification-handler"
BATCH_SIZE = 300
MAX_PULL_SEC=60

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_messages(subscriber: SubscriberClient, sub_path:str) -> List[ReceivedMessage]:
    """get a large batch of messages from the pubsub topic"""

    collected_msgs: List[ReceivedMessage] = []
    start_time = time.time()

    while ( #loop to try to collect large batch of messages
        len(collected_msgs)< BATCH_SIZE #stop if enough messages are found
        and time.time() -start_time < MAX_PULL_SEC #stop if we have been waiting too long
        ):
            
        #keep trying to acquire messages
        response = subscriber.pull(
            request={
                "subscription": sub_path,
                "max_messages": BATCH_SIZE,
            }
        )
        if not response.received_messages:
            logger.debug("Stopped pulling due to no messages recieved")
            break #stop loop if there are no more messages

        collected_msgs.extend(response.received_messages)

    return collected_msgs


def main():

    # TODO remove later
    try:
        archives, cats = get_all_moderators()
        logger.info(f"DB check OK: {len(archives)} archive entries, {len(cats)} category entries")
    except Exception:
        logger.exception("DB check FAILED — cannot connect to database")
        raise

    #get messages
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    messages=get_messages(subscriber, subscription_path)
    if len(messages)==0:
        logger.warning("No messages found.")
        return

    #collect data
    to_ack=process_messages(messages)

    #acknowledge all
    subscriber.acknowledge(
        request={
            "subscription": subscription_path,
            "ack_ids": to_ack,
        }
    )


if __name__ == "__main__":
    main()