"""entrypoint for the daily_update job: once-a-day digest for moderators who don't want notifications as they happen

STUB — not implemented. no pubsub, this job is scheduled and gets its content from a db query.
"""

import logging

from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok

setup_logging()
logger = logging.getLogger(__name__)


def main():

    #fail fast on email misconfiguration before doing any work
    if not email_config_ok():
        return

    logger.info("hello world from daily_update")

    #TODO query the submissions to report on, resolve which moderators want a daily digest via
    #app.shared.moderators, then render and send one email per moderator


if __name__ == "__main__":
    main()
