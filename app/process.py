"""processes notifications"""
import logging
import json

from google.pubsub import ReceivedMessage

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE

from app.email import send_email
from app.schema import NotificationParams, SimplifiedNotification, ConsolidatedNotifications, EmailTask, NotificationType, CommentData, PromoteData, NewPropData, PropRespData
from app.moderators import get_all_moderators, get_recipient_ids_for_categories, get_mod_emails

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_message(payload)-> tuple[NotificationParams, SimplifiedNotification]:
    """turn pubsub payload insto structured data, raises an error if data is badly formed"""
    full_note = NotificationParams.model_validate(payload)

    match full_note.action:
        case NotificationType.COMMENT:
            data = CommentData.model_validate(full_note.data)   
        case NotificationType.NEW_PROP:
            data = NewPropData.model_validate(full_note.data)
        case NotificationType.PROMOTE:
            data = PromoteData.model_validate(full_note.data)
        case NotificationType.PROP_RESP:
            data = PropRespData.model_validate(full_note.data)
        case _:
            logging.error(f"unhandled action type: {full_note.action}, skipping message")
            raise ValueError(f"unhandled action: {full_note.action}")

    simple_note=SimplifiedNotification(time=full_note.time, data=data)
    return full_note, simple_note

def _convert_messages(messages:list[ReceivedMessage]) ->  tuple[dict[int, ConsolidatedNotifications], list[str]]:
    """manages turning the recieved pubsub messages into consolidated data on submissions with notifications"""

    failed_parse_acks: list[str] = [] #parse failures: always ack, won't fix on retry
    all_notifications: dict[int, ConsolidatedNotifications]={} #tracks all notifications for each submission

    #convert each message and store in lists
    for msg in messages:

        #validation and error handling
        try:
            payload = json.loads(msg.message.data.decode("utf-8"))
            full_note, simple_note = _parse_message(payload)
        except Exception as e:
            logging.error(f"[PARSE FAILURE] {e} — msg: {msg.message.data}")
            failed_parse_acks.append(msg.ack_id) #ack parse failures so they don't repeat
            continue

        #convert and store
        categories: set[Category]=set()
        for cat in full_note.categories:
            try:
                categories.add(CATEGORIES_ACTIVE[cat])
            except KeyError:
                logging.error(f"unknown category: {cat}, skipping")

        id=full_note.submission_id
        sub_notes = all_notifications.get(id, ConsolidatedNotifications(submission_id=id))
        sub_notes.ack_ids.append(msg.ack_id) #ack only after successful email send
        sub_notes.user_ids.add(full_note.user_id)
        sub_notes.changes.append(simple_note)
        sub_notes.categories.update(categories)

        all_notifications[id]=sub_notes

    return all_notifications, failed_parse_acks

def _build_email_tasks(all_notifications: dict[int, ConsolidatedNotifications]) -> list[EmailTask]:
    if not all_notifications:
        logger.info("No notifications to process")
        return []

    #collect all the categories and emails
    archives, cats = get_all_moderators()

    all_categories: set[Category] = set()
    for notifications in all_notifications.values():
        all_categories.update(notifications.categories)

    per_cat, all_user_ids = get_recipient_ids_for_categories(all_categories, archives, cats)
    ids_to_email = get_mod_emails(all_user_ids)

    #build individual email tasks
    tasks = []
    for sub_id, notifications in all_notifications.items():
        email_ids: set[int] = set()
        reply_ids: set[int] = set()
        #everyone to email
        for cat in notifications.categories:
            e, r = per_cat.get(cat.id, (set(), set()))
            email_ids.update(e)
            reply_ids.update(r)
        # don't email the sole actor about their own changes
        if len(notifications.user_ids) == 1:
            sole_actor = next(iter(notifications.user_ids))
            email_ids.discard(sole_actor)

        to_emails = [ids_to_email[uid] for uid in email_ids if uid in ids_to_email]
        reply_to = [ids_to_email[uid] for uid in reply_ids if uid in ids_to_email] or None

        missing = (email_ids | reply_ids) - ids_to_email.keys()
        if missing:
            logger.error(f"submission {sub_id}: no tapir_users row for moderator ids {missing}")

        if not to_emails:
            logger.info(f"submission {sub_id}: no recipients after exclusions, skipping")
            continue

        #email data
        tasks.append(EmailTask(
            submission_id=sub_id,
            to_emails=to_emails,
            reply_to_emails=reply_to,
            notifications=notifications,
        ))
    return tasks


def process_messages(messages:list[ReceivedMessage])->list[str]:
    """handles the overall message processing"""

    #turn messages into data
    all_notifications, failed_parse_acks = _convert_messages(messages)
    final_acks = list(failed_parse_acks)

    if not all_notifications:
        logger.info("No valid notifications after parsing, nothing to send")
        return final_acks

    #determine who to email what
    email_tasks = _build_email_tasks(all_notifications)
    if not email_tasks:
        logger.info("No emails to send")
        return final_acks

    #send emails
    for task in email_tasks:
        try:
            send_email(
                to_emails=task.to_emails,
                subject=f"Notification for submission {task.submission_id}",
                body="TBD",
                reply_to_emails=task.reply_to_emails,
            )
            final_acks.extend(task.notifications.ack_ids) #ack only on success
        except Exception:
            logger.exception(f"Failed to send email for submission {task.submission_id}, will redeliver")

    #test logging
    logger.info(f"Processed {len(final_acks)} messages. Sent {len(email_tasks)} (hypothetical) emails.")

    #make sure to acknowledge when done
    return final_acks