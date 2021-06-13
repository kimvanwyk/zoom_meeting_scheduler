from collections import namedtuple

import zoom

import arrow
import inquirer


def get_month_list():
    """Return a list of the next 12 months relative to the current month"""
    month = arrow.utcnow()
    months = []
    for d in range(12):
        months.append((month.format("MMM YYYY"), month))
        month = month.shift(months=+1)
    return months


def ask_questions():

    questions = [
        inquirer.Text(
            "topic",
            "Meeting topic",
        ),
        inquirer.Text(
            "requestor_name",
            "Meeting requestor name",
        ),
        inquirer.Text(
            "requestor_email",
            "Meeting requestor email",
        ),
        inquirer.List("month", "Meeting month", get_month_list()),
        inquirer.Text(
            "day",
            "Meeting day",
        ),
        inquirer.Text(
            "time",
            "Meeting time (HH:MM)",
        ),
        inquirer.Text(
            "duration",
            "Meeting duration (minutes)",
        ),
    ]
    answers = inquirer.prompt(questions)
    dt = answers["month"]
    print(dt)
    (hour, minute) = [int(c) for c in answers["time"].split(":")]
    dt = dt.replace(
        day=int(answers["day"]), hour=hour, minute=minute, second=0, microsecond=0
    )
    return zoom.MEETING_CONFIG(
        answers["topic"],
        answers["requestor_name"],
        answers["requestor_email"],
        dt,
        int(answers["duration"]),
    )


def make_meeting(mc):
    meeting = zoom.make_meeting(mc)
    return meeting


if __name__ == "__main__":
    mc = ask_questions()
    print(mc)
    print(make_meeting(mc))
