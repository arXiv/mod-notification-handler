from datetime import datetime
from typing import Literal, Union
from enum import Enum
from pydantic import BaseModel
from dataclasses import dataclass, field

from arxiv.taxonomy.category import Category

class NotificationType(str, Enum):
    COMMENT = 'Comment Added'
    PROP_RESP = 'Category Proposal Responses'
    NEW_PROP = 'New Category Proposal'
    PROMOTE = 'Category Promotion'
    #TODO should rejections eventually send emails?

#the shape the data comes in the pubsub message
class NotificationParams(BaseModel):
    time: datetime # time action was done #TODO add to modapi
    submission_id: int
    user_id: int # id of user who created notification
    categories: list[str] #categories who should recieve the notification
    action: NotificationType
    data: dict

class CommentData(BaseModel):
    comment: str

class PropRespData(BaseModel):
    responses: str
    category_change: str

class NewPropData(BaseModel):
    msg: str

class PromoteData(BaseModel):
    category: str
    promotion_type: Literal["primary", "secondary"]
    category_change: str


class SimplifiedNotification(BaseModel):
    time: datetime
    data: Union[CommentData, PromoteData, PropRespData, NewPropData]

@dataclass
class ConsolidatedNotifications:
    submission_id: int
    categories: set[Category] =field(default_factory=set) #categories to notify about this submission
    user_ids: set[int] = field(default_factory=set)  # users responsible for these notifications
    changes: list[SimplifiedNotification] = field(default_factory=list) #all notifications for a particular submission