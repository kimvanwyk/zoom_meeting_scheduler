from collections import namedtuple
import os

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
    requestor_name = inquirer.text(message="Meeting requestor name").execute()
    requestor_email = inquirer.text(message="Meeting requestor email").execute()
    dt = inquirer.select(message="Meeting month", choices=get_month_list()).execute()
    day = int(
        inquirer.text(message="Meeting day", validate=NumberValidator()).execute()
    )
    (hour, minute) = inquirer.text(
        message="Meeting time (HH:MM)",
        validate=lambda text: len(text) == 5
        and text[2] == ":"
        and all([text[i] in "012456789" for i in (0, 1, 3, 4)]),
        invalid_message="Value should be in format HH:MM",
        filter=lambda x: [int(c) for c in x.split(":")],
    ).execute()
    duration = int(
        inquirer.text(
            message="Meeting duration (minutes)", validate=NumberValidator()
        ).execute()
    )
    dt = dt.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)

    return zoom.MEETING_CONFIG(
        topic,
        requestor_name,
        requestor_email,
        dt,
        duration,
    )


def make_meeting(mc):
    meeting = zoom.make_meeting(mc)
    return meeting


def print_message(meeting_config, meeting_details):
    with open("email.txt", "r") as fh:
        template = fh.read()

    time = f"{mc.start_datetime:DD MMM YYYY} at {mc.start_datetime:HH:mm} to {mc.start_datetime.shift(minutes=+mc.duration):HH:mm}"

    subject = f'"{mc.topic}" Zoom meeting for {time}'
    msg = template.format(
        **{
            "name": mc.requester_name.split(" ")[0],
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
    m = make_meeting(mc)
    print_message(mc, m)