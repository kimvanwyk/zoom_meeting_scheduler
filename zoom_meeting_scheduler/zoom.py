import models

from collections import namedtuple
import datetime
import os
from random import randint

from authlib.jose import jwt
from dotenv import load_dotenv
import requests
from rich import print

load_dotenv()

AUTH_HEADER = {"Host": "zoom.us"}
AUTH_DATA = {
    "grant_type": "account_credentials",
    "account_id": os.getenv("ZOOM_ACCOUNT_ID"),
}
AUTH_CREDENTIALS = (os.getenv("ZOOM_CLIENT_ID"), os.getenv("ZOOM_CLIENT_SECRET"))

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


def get_token():
    res = requests.post(
        "https://zoom.us/oauth/token",
        data=AUTH_DATA,
        headers=AUTH_HEADER,
        auth=AUTH_CREDENTIALS,
    )
    return res.json()["access_token"]


def get_auth_headers():
    token = get_token()
    return {
        "content-type": "application/json",
        "authorization": f"Bearer {token}",
    }


def make_meetings(meeting_config):
    auth_headers = get_auth_headers()

    for meeting in meeting_config.meetings:
        passcode = randint(100000, 999999)
        data = DEFAULTS.copy()
        data["topic"] = meeting_config.topic
        data["start_time"] = meeting.meeting_time.datetime.format("YYYY-MM-DDTHH:mm:ss")
        data["duration"] = meeting.meeting_time.duration
        data[
            "agenda"
        ] = f"Requester: {meeting_config.requester.name} (Email: {meeting_config.requester.email})"
        data["password"] = passcode

        res = requests.post(
            f"https://api.zoom.us/v2/users/me/meetings",
            json=data,
            headers=auth_headers,
        )
        res.raise_for_status()

        json = res.json()
        meeting.zoom_meeting = models.ZoomMeeting(
            id=json["id"], join_url=json["join_url"], passcode=passcode
        )
    return meeting_config


def list_recordings(start, end):
    auth_headers = get_auth_headers()
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    res = requests.get(
        f"https://api.zoom.us/v2/users/me/recordings",
        headers=auth_headers,
        params={"page_size": 300, "from": start, "to": end},
    )
    res.raise_for_status()

    return res.json()["meetings"]


def download_recording(recording):
    auth_headers = get_auth_headers()
    fn = f'{recording["topic"].replace(" ", "_").lower()}_{recording["start_time"].replace("-","").replace(":","").lower()}.mp4'
    for rec in recording["recording_files"]:
        if rec["file_type"] == "MP4":
            with requests.get(
                rec["download_url"], headers=auth_headers, stream=True
            ) as r:
                r.raise_for_status()
                with open(fn, "wb") as fh:
                    for chunk in r.iter_content(chunk_size=8192):
                        fh.write(chunk)
    return fn


if __name__ == "__main__":
    import json

    print(get_auth_headers())
    # recordings = list_recordings()
    # print(download_recording(recordings[0]))

    # res = requests.get(
    #     "https://api.zoom.us/v2/users/me/meetings?type=scheduled&page_size=100",
    #     headers=get_auth_headers(),
    # )
    # print("All meetings")
    # with open("meetings.json", "w") as fh:
    #     json.dump(res.json(), fh)
