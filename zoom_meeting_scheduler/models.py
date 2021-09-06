import arrow
from pydantic import BaseModel, HttpUrl


class MeetingTime(BaseModel, arbitrary_types_allowed=True):
    datetime: arrow.Arrow
    duration: int


class Meeting(BaseModel):
    id: int
    join_url: HttpUrl
    passcode: int
