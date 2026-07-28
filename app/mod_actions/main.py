"""entrypoint for the mod_actions job: emails moderators about actions taken on submissions"""

import logging

from google.cloud import pubsub_v1

from app.shared.config import settings
from app.shared.utils.log import setup_logging
from app.shared.pubsub import get_messages
from app.shared.utils.startup import email_config_ok
from app.mod_actions.process import process_messages

setup_logging()
logger = logging.getLogger(__name__)


def main():

    #fail fast on email misconfiguration before touching the queue
    if not email_config_ok():
        return

    #get messages
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(settings.GCP_PROJECT_ID, settings.PUBSUB_SUBSCRIPTION_ID_MOD_ACTIONS)
    messages=get_messages(subscriber, subscription_path)
    if len(messages)==0:
        logger.info("0 messages found.")
        return

    def ack(ids: list[str]) -> None:
        subscriber.acknowledge(request={"subscription": subscription_path, "ack_ids": ids})

    process_messages(messages, ack_fn=ack)


if __name__ == "__main__":
    main()
