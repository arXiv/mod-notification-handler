"""entrypoint for the daily_update job: a once-a-day digest of open submissions for moderators who
asked for one.
"""
import logging

from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok
from app.daily_update.process import send_daily_reports

setup_logging()
logger = logging.getLogger(__name__)


def main():

    if not email_config_ok():
        return

    #TODO reimplement arxiv holiday skip?
    # TODO skip weekends? 
    send_daily_reports()


if __name__ == "__main__":
    main()
