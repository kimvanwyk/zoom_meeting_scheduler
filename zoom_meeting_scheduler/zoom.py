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


def list_meetings(start, end, typ="upcoming_meetings"):
    auth_headers = get_auth_headers()
    start = start.strftime("%Y-%m-%d")
    end = end.strftime("%Y-%m-%d")
    res = requests.get(
        "https://api.zoom.us/v2/users/me/meetings",
        headers=auth_headers,
        params={
            "page_size": 300,
            "from": start,
            "to": end,
            "type": typ,
        },
    )
    res.raise_for_status()

    return res.json()["meetings"]


def get_meeting(meeting_id):
    auth_headers = get_auth_headers()
    res = requests.get(
        f"https://api.zoom.us/v2//meetings/{meeting_id}",
        headers=auth_headers,
    )
    res.raise_for_status()

    return res.json()


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


def get_meeting_recordings(meeting_id):
    auth_headers = get_auth_headers()
    res = requests.get(
        f"https://api.zoom.us/v2/meetings/{meeting_id}/recordings",
        headers=auth_headers,
    )
    if res.status_code == 404:
        return None
    res.raise_for_status()

    return res.json()


def download_recording_file(recording_file, filename):
    auth_headers = get_auth_headers()
    fn = f"{filename}.{recording_file['file_extension'].lower()}"
    res = requests.get(
        recording_file["download_url"],
        headers=auth_headers,
    )
    with open(fn, "wb") as fh:
        fh.write(res.content)


def list_recordings(start, end):
    auth_headers = get_auth_headers()
    auth_headers["scopes"] = "recording:read:admin"
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

    # meetings = list_meetings(
    #     datetime.datetime.now(), datetime.datetime.now() + datetime.timedelta(weeks=12)
    # )
    if 0:
        meetings = list_meetings(
            datetime.datetime(day=1, month=7, year=2025),
            datetime.datetime(day=1, month=7, year=2026),
        )

        for m in meetings:
            print(m["topic"])
            print(m["id"])
            m = get_meeting_recordings(m["id"])
            if m:
                for rf in m["recording_files"]:
                    print(rf["download_url"])

    if 0:
        reqs = [
            "2025-08-26",
            "2025-09-30",
            "2025-10-28",
            "2025-11-25",
            "2026-01-27",
            "2026-02-24",
            "2026-03-31",
            "2026-04-28",
            "2026-05-26",
            "2026-06-30",
        ]

        meetings = list_meetings(
            datetime.datetime(day=25, month=8, year=2025),
            datetime.datetime(day=1, month=7, year=2026),
        )

        for m in meetings:
            if any([t in m["start_time"] for t in reqs]):
                print(m["topic"])
                print(m["start_time"])
    if 0:
        ids = [81048019829]
        for i in ids:
            m = get_meeting_recordings(i)
            if m:
                filename = m["topic"].lower().replace(" ", "_")
                print(filename)
                os.makedirs(filename, exist_ok=True)
                os.chdir(filename)
                for n, rf in enumerate(m["recording_files"], 1):
                    download_recording_file(rf, f"{filename}_{n:02}")
                os.chdir("../")

    if 0:
        dt = datetime.datetime.now()
        recordings = list_recordings(dt - datetime.timedelta(days=365), dt)
        for d in recordings:
            print(d["topic"])
            for rf in d["recording_files"]:
                print(rf["download_url"])
    # print(download_recording(recordings[0]))

    # res = requests.get(
    #     "https://api.zoom.us/v2/users/me/meetings?type=scheduled&page_size=100",
    #     headers=get_auth_headers(),
    # )
    # print("All meetings")
    # with open("meetings.json", "w") as fh:
    #     json.dump(res.json(), fh)

    if 0:
        meetings = list_meetings(
            datetime.datetime(day=1, month=7, year=2025),
            datetime.datetime(day=1, month=7, year=2026),
        )
        for m in meetings:
            print(m["topic"])
        print(len(meetings))

    if 1:
        # from glt_meetings import meetings
        # requester = models.Requester(
        #     name="Patrick Mills", email="patrick.mills@za.saabgroup.com"
        # )

        # from strengthen_410e_meetings import meetings
        # requester = models.Requester(name="Patrick Gamedze", email="patg@swazi.net")

        # from cabinet_meetings import meetings

        # requester = models.Requester(
        #     name="Rowan Tuckett", email="rowan.tuckett@lions410e.org.za"
        # )

        # from gmt_get_meetings import meetings

        # requester = models.Requester(
        #     name="Sanet Emmerick", email="admin@definefs.co.za"
        # )

        from training_meetings import meetings

        requester = models.Requester(name="Lindie van Wyk", email="lindie@faerie.co.za")

        if 0:
            for topic, dt, duration in meetings:
                print(dt)
                for m in list_meetings(dt, dt):
                    print(f'{m["topic"]} ({m["start_time"]}) ({m["duration"]} hr(s))')
                    print(m["join_url"])
                    print()
                print()

        if 1:
            for topic, dt, duration in meetings:
                mt = models.MeetingTime(
                    datetime=models.arrow.get(dt), duration=duration
                )
                mc = models.MeetingConfig(
                    topic=topic,
                    requester=requester,
                    meetings=[models.Meeting(meeting_time=mt)],
                )
                make_meetings(mc)
                meeting = mc.meetings[0]
                print(
                    f"{mc.topic} ({meeting.meeting_time.datetime.datetime:%Y/%m/%d %H:%M} ({meeting.meeting_time.duration} hrs)"
                )
                print(f"Link: {meeting.zoom_meeting.join_url}")
                print(f"Passcode: {meeting.zoom_meeting.passcode}")
                print()

    if 0:
        print(get_meeting(81660399912))
