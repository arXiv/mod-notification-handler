"""processes notifications"""
import logging
from datetime import datetime
from typing import cast, Tuple
import json

from google.pubsub import ReceivedMessage

from app.schema import NotificationParams, SimplifiedNotification, ConsolidatedNotifications, NotificationType, CommentData, PromoteData, NewPropData, PropRespData

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _parse_message(payload)-> Tuple[NotificationParams, SimplifiedNotification]:
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

def process_messages(messages:list[ReceivedMessage])->list[str]:
    ack_ids: list[str] = [] #track messages to be acknowledged 
    all_notifications: dict[int, ConsolidatedNotifications]={} #tracks all notifications for each submission 
    timestamps: list[str] = []

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
            

        #convert
        message = msg.message
        dt= cast(datetime, message.publish_time) #weird issue with timestamp typing at runtime
        #store
        timestamps.append(dt.strftime("%H:%M"))
        
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

    logger.info(f"Processed {len(ack_ids)} messages. Timestamps: {', '.join(timestamps)}")
    return ack_ids