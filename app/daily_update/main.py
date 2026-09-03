"""entrypoint for the daily_update job: a once-a-day digest of open submissions for moderators who
asked for one.
"""
import logging

from app.shared.utils.log import setup_logging
from app.shared.utils.startup import email_config_ok
from app.daily_update.announce import is_holiday_today
from app.daily_update.process import send_daily_reports

setup_logging()
logger = logging.getLogger(__name__)


def main():

    if not email_config_ok():
        return

    #weekends are the scheduler's job — it runs weekdays only, as the legacy perl cron did
    if is_holiday_today():
        logger.info("today is an arXiv holiday,no digest is sent")
        return

    send_daily_reports()


if __name__ == "__main__":
    main()
