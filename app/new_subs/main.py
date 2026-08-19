"""entrypoint for the new_subs job: emails moderators about new submissions

STUB — not implemented. see app/mod_actions/main.py for the shape of a working pubsub job.
"""

import logging

from app.shared.config import settings
from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok

setup_logging()
logger = logging.getLogger(__name__)


def main():

    #fail fast on email misconfiguration before touching the queue
    if not email_config_ok():
        return

    logger.info(f"hello world from new_subs — subscription: {settings.PUBSUB_SUBSCRIPTION_ID_NEW_SUBS}")

    #TODO pull from PUBSUB_SUBSCRIPTION_ID_NEW_SUBS with app.shared.pubsub.get_messages, parse into
    #this job's own schema, then build and send emails. moderator lookup comes from app.shared.moderators


if __name__ == "__main__":
    main()
