from datetime import datetime
from typing import List, Any, Set
from enum import Enum

from arxiv.taxonomy.category import Category

class NotificationType(str, Enum):
    COMMENT = 'Comment Added'
    PROP_RESP = 'Category Proposal Responses'
    NEW_PROP = 'New Category Proposal'
    PROMOTE = 'Category Promotion'
    #TODO should rejections eventually send emails?

#the shape of the incoming notification data
class NotificationParams:
    time: datetime # time action was done #TODO add to modapi
    submission_id: int
    user_id: int # id of user who created notification
    categories: List[str] #categories who should recieve the notification
    action: NotificationType #the type of notification this is TODO modapi will have to update to this
    data: Any #format of data varies based on message type

class SimplifiedNotification:
    action: NotificationType
    time: datetime
    data: Any #format of data varies based on message type

class ConsolidatedNotifications:
    submission_id: int
    categories: Set[Category] #categories to notify about this submission
    user_ids: Set[int] # users responsible for these notifications
    changes: List[SimplifiedNotification] #all notifications for a particular submission