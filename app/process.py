"""processes notifications"""
import logging
import json

from google.pubsub import ReceivedMessage

from arxiv.taxonomy.category import Category
from arxiv.taxonomy.definitions import CATEGORIES_ACTIVE
from app.schema import NotificationParams, SimplifiedNotification, ConsolidatedNotifications, NotificationType, CommentData, PromoteData, NewPropData, PropRespData

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
        payload = json.loads(msg.message.data)
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

def process_messages(messages:list[ReceivedMessage])->list[str]:
    """handles the overall message processing"""

    all_notifications, ack_ids=_convert_messages(messages)
        
    email_data=[]
    #go through each submission
    for sub_id, notifications in all_notifications.items():
        #assemble individual message for sumbission
        #build email
        #figure out who to email
        pass

    #send emails
    for item in email_data:
        pass

    comment_count=0
    prop_count=0
    prop_resp_count=0
    promote_count=0
    
    for _, data in all_notifications.items():
        for change in data.changes:
            if isinstance(change.data, CommentData):
                comment_count += 1
            elif isinstance(change.data, NewPropData):
                prop_count += 1
            elif isinstance(change.data, PropRespData):
                prop_resp_count += 1
            elif isinstance(change.data, PromoteData):
                promote_count += 1


    logger.info(f"Processed {len(ack_ids)} messages. {comment_count} comments, {prop_count} proposals, {prop_resp_count} responses, and {promote_count} promotions across {len(all_notifications.keys())} submisions")
    return ack_ids