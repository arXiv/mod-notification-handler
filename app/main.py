import logging
from google.cloud import pubsub_v1

PROJECT_ID = "arxiv-development"
SUBSCRIPTION_ID = "mod-notification-handler"
BATCH_SIZE = 300

logging.basicConfig(level=logging.INFO)


def main():
    logger = logging.getLogger(__name__)

    #get messages
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(PROJECT_ID, SUBSCRIPTION_ID)
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": BATCH_SIZE,
        }
    )
    if not response.received_messages:
        logger.warning("No messages found.")
        return

    #collect data
    ack_ids = []
    timestamps = []

    for msg in response.received_messages:
        message = msg.message
        timestamps.append(str(message.publish_time))
        ack_ids.append(msg.ack_id)

    logger.info(f"Caught {len(ack_ids)} messages")
    logger.info(f"Timestamps: {', '.join(timestamps)}")

    #acknowledge all
    subscriber.acknowledge(
        request={
            "subscription": subscription_path,
            "ack_ids": ack_ids,
        }
    )

    logger.info("Messages acknowledged")


if __name__ == "__main__":
    main()