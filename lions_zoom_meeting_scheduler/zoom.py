import arrow

from collections import namedtuple
import datetime
import os
from random import randint

from authlib.jose import jwt
from dotenv import load_dotenv
import requests

load_dotenv()

MEETING_CONFIG = namedtuple(
    "MeetingConfig",
    ("topic", "requester_name", "requester_email", "start_datetime", "duration"),
)
MEETING = namedtuple("Meeting", ("id", "join_url", "passcode"))

JWT_HEADER = {"alg": "HS256", "typ": "JWT"}
JWT_PAYLOAD = {"iss": os.getenv("ZOOM_API_KEY")}

DEFAULTS = {
    "type": 2,
    "timezone": None,
    "settings": {
        "host_video": False,
        "participant_video": False,
        "join_before_host": True,
        "jbh_time": 0,
        "mute_upon_entry": True,
        "auto_recording": "none",
        "meeting_authentication": False,
    },
}


def get_auth_headers():
    exp = datetime.datetime.now() + datetime.timedelta(hours=1)
    JWT_PAYLOAD["exp"] = exp
    s = jwt.encode(JWT_HEADER, JWT_PAYLOAD, os.getenv("ZOOM_API_SECRET"))
    return {
        "content-type": "application/json",
        "authorization": f"Bearer {str(s)[2:-1]}",
    }


def make_meeting(meeting_config):
    auth_headers = get_auth_headers()

    passcode = randint(100000, 999999)
    data = DEFAULTS.copy()
    data["topic"] = meeting_config.topic
    data["start_time"] = meeting_config.start_datetime.format("YYYY-MM-DDTHH:mm:ss")
    data["duration"] = meeting_config.duration
    data["agenda"] = f"Requester Email: {meeting_config.requester_email}"
    data["password"] = passcode

    res = requests.post(
        f"https://api.zoom.us/v2/users/{os.getenv('ZOOM_USER_ID')}/meetings",
        json=data,
        headers=auth_headers,
    )
    res.raise_for_status()

    json = res.json()
    return MEETING(json["id"], json["join_url"], passcode)


if __name__ == "__main__":
    res = requests.get(
        "https://api.zoom.us/v2/users?status=active&page_size=30&page_number=1",
        headers=auth_headers,
    )
    print("Active user request")
    print(res.json())
