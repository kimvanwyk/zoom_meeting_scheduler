import arrow
from pydantic import BaseModel, HttpUrl

from typing import List


class MeetingTime(BaseModel, arbitrary_types_allowed=True):
    datetime: arrow.Arrow
    duration: int


class Requester(BaseModel):
    name: str
    # email is deliberately str not a validated email field as the value need not be set
    email: str


class MeetingConfig(BaseModel):
    topic: str
    requester: Requester


class ZoomMeeting(BaseModel):
    id: int
    join_url: HttpUrl
    passcode: int


class Meeting(BaseModel):
    meeting_time: MeetingTime
    zoom_meeting: ZoomMeeting
