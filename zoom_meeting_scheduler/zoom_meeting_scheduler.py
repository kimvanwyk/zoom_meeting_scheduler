import os

import models
import zoom

import arrow
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
import pyperclip


def get_month_list():
    """Return a list of the next 12 months relative to the current month"""
    month = arrow.utcnow()
    months = []
    for d in range(12):
        months.append({"name": month.format("MMM YYYY"), "value": month})
        month = month.shift(months=+1)
    return months


def ask_questions():
    topic = inquirer.text(message="Meeting topic").execute()
    requester_name = inquirer.text(message="Meeting requester name").execute()
    requester_email = inquirer.text(message="Meeting requester email").execute()
    meeting_times = []
    cont = True
    while cont:
        dt = inquirer.select(
            message="Meeting month", choices=get_month_list()
        ).execute()
        day = int(
            inquirer.text(message="Meeting day", validate=NumberValidator()).execute()
        )
        (hour, minute) = inquirer.text(
            message="Meeting time (HH:MM)",
            validate=lambda text: len(text) == 5
            and text[2] == ":"
            and all([text[i] in "0123456789" for i in (0, 1, 3, 4)]),
            invalid_message="Value should be in format HH:MM",
            filter=lambda x: [int(c) for c in x.split(":")],
        ).execute()
        duration = int(
            inquirer.text(
                message="Meeting duration (minutes)", validate=NumberValidator()
            ).execute()
        )
        meeting_times.append(
            models.MeetingTime(
                datetime=dt.replace(
                    day=day, hour=hour, minute=minute, second=0, microsecond=0
                ),
                duration=duration,
            )
        )
        cont = inquirer.confirm(message="Add another meeting?", default=False).execute()

    return models.MeetingConfig(
        topic=topic,
        requester=models.Requester(name=requester_name, email=requester_email),
        meeting_times=meeting_times,
    )


def make_meeting(mc):
    meeting = zoom.make_meeting(mc)
    return meeting


def print_message(meeting_config, meeting_details):
    with open("email.txt", "r") as fh:
        template = fh.read()

    time = f"{mc.meeting_time.datetime:DD MMM YYYY} at {mc.meeting_time.datetime:HH:mm} to {mc.meeting_time.datetime.shift(minutes=+mc.meeting_time.duration):HH:mm}"

    subject = f'"{mc.topic}" Zoom meeting for {time}'
    msg = template.format(
        **{
            "name": mc.requester.name.split(" ")[0],
            "topic": mc.topic,
            "link": m.join_url,
            "time": time,
            "passcode": m.passcode,
            "username": os.getenv("ZOOM_USERNAME"),
            "password": os.getenv("ZOOM_PASSWORD"),
        }
    )
    print(f"Subject: {subject}")
    pyperclip.copy(subject)
    input()
    print("Message:")
    print(msg)
    pyperclip.copy(msg)
    input()


if __name__ == "__main__":
    mc = ask_questions()
    # m = make_meeting(mc)
    # print_message(mc, m)
    print(mc)
