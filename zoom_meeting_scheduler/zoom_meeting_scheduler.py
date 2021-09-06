import os

import models
import zoom

import arrow
from InquirerPy import inquirer
from InquirerPy.validator import NumberValidator
from jinja2 import Environment, FileSystemLoader, select_autoescape
import pyperclip
from rich import print

JINJA_ENV = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(),
)

TEMPLATE = JINJA_ENV.get_template("email.txt")


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
        meetings=[models.Meeting(meeting_time=mt) for mt in meeting_times],
    )


def make_meetings(meeting_config):
    mc = zoom.make_meetings(meeting_config)
    return meeting_config


def print_message(meeting_config):
    plural = len(meeting_config.meetings) > 1
    meetings = []
    for meeting in meeting_config.meetings:
        dt = meeting.meeting_time.datetime
        meetings.append(
            {
                "time": f"{dt:DD MMM YYYY} at {dt:HH:mm} to {dt.shift(minutes=+meeting.meeting_time.duration):HH:mm}",
                "link": meeting.zoom_meeting.join_url,
                "passcode": meeting.zoom_meeting.passcode,
            }
        )

    subject = f'"{meeting_config.topic}" Zoom meeting{"s" if plural else ""}'
    msg = TEMPLATE.render(
        {
            "plural": plural,
            "name": meeting_config.requester.name.split(" ")[0],
            "topic": meeting_config.topic,
            "meetings": meetings,
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
    (mc) = ask_questions()
    mc = make_meetings(mc)
    print_message(mc)
