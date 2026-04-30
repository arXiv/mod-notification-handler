"""processes notifications"""
import logging
from datetime import datetime
from typing import List, cast, Dict

from google.pubsub import ReceivedMessage

from app.schema import NotificationParams, SimplifiedNotification, ConsolidatedNotifications

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_messages(messages:List[ReceivedMessage])->List[str]:
    ack_ids: List[str] = [] #track messages to be acknowledged 
    all_notifications: Dict[int, ConsolidatedNotifications]={} #tracks all notifications for each submission 
    timestamps: List[str] = []

    #convert each message and store in lists
    for msg in messages:
        ack_ids.append(msg.ack_id)

        #validation and error handling
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