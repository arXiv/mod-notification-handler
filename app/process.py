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

    simple_note=SimplifiedNotification(time=full_note.time, data=data)
    return full_note, simple_note

def _convert_messages(messages:list[ReceivedMessage]) ->  tuple[dict[int, ConsolidatedNotifications], list[str]]:
    """manages turning the recieved pubsub messages into consolidated data on submissions with notifications"""

    ack_ids: list[str] = [] #track messages to be acknowledged 
    all_notifications: dict[int, ConsolidatedNotifications]={} #tracks all notifications for each submission 

    #convert each message and store in lists
    for msg in messages:
        ack_ids.append(msg.ack_id)

        #validation and error handling
        payload = json.loads(msg.message.data.decode("utf-8"))
        try:
            full_note, simple_note = _parse_message(payload)
        except Exception as e:
            logging.error(f"failed to parse message: error: {e} msg:{payload}")
            #don't raise error acknowledge unparseable message anyways so it doesnt repeat
            continue
            
        #convert and store
        try:
            categories: set[Category]=set()
            for cat in full_note.categories:
                categories.add(CATEGORIES_ACTIVE[cat])
        except Exception as e:
            logging.error(f"bad category: {cat}")

        id=full_note.submission_id
        sub_notes = all_notifications.get(id, ConsolidatedNotifications(submission_id=id))
        sub_notes.user_ids.add(full_note.user_id)
        sub_notes.changes.append(simple_note)
        sub_notes.categories.update(categories)

        all_notifications[id]=sub_notes

    return all_notifications, ack_ids

def _build_email_tasks(all_notifications: dict[int, ConsolidatedNotifications]) -> list[EmailTask]:
    if not all_notifications:
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
        #email data
        tasks.append(EmailTask(
            submission_id=sub_id,
            to_emails=[ids_to_email[uid] for uid in email_ids],
            reply_to_emails=[ids_to_email[uid] for uid in reply_ids] or None,
            notifications=notifications,
        ))
    return tasks


def process_messages(messages:list[ReceivedMessage])->list[str]:
    """handles the overall message processing"""

    #turn messages into data
    all_notifications, ack_ids=_convert_messages(messages)

    #determine who to email what
    email_tasks=_build_email_tasks(all_notifications)

    #send emails
    for task in email_tasks:
        send_email(
            to_emails=task.to_emails,
            subject=f"Notification for submission {task.submission_id}",
            body="TBD",
            reply_to_emails=task.reply_to_emails,
        )

    #test logging
    logger.info(f"Processed {len(ack_ids)} messages. Sent {len(email_tasks)} (hypothetical) emails.")

    #make sure to acknowledge when done
    return ack_ids