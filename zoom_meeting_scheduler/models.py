import arrow
from pydantic import BaseModel


class MeetingTime(BaseModel, arbitrary_types_allowed=True):
    # url to check for reachability. Do not include query params in this url, to prevent sensitive data being displayed in debug
    datetime: arrow.Arrow
    duration: int
