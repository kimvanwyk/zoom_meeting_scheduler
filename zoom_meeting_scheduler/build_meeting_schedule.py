from collections import defaultdict

import arrow
from rich import print

import zoom

EXCLUDED_IDS = (81878881659, 86823702954, 81660399912)
end_date = arrow.get()
if end_date.month <= 6:
    end_date = end_date.shift(years=-1)
end_date = end_date.replace(month=6, day=30)
meetings = {}
for chunks in range(6):
    start_date = end_date.shift(days=1)
    end_date = end_date.shift(months=3)
    end_date = end_date.replace(day=1)
    end_date = end_date.shift(days=-1)
    for typ in (
        "previous_meetings",
        "upcoming_meetings",
        "upcoming",
        "scheduled",
        "live",
    ):
        for meeting in zoom.list_meetings(
            start_date.datetime, end_date.datetime, typ=typ
        ):
            if meeting["id"] not in EXCLUDED_IDS:
                meetings[meeting["id"]] = meeting

sorted_meetings = defaultdict(list)
for meeting in meetings.values():
    dt = arrow.get(meeting["start_time"])
    dt = dt.shift(hours=2)
    time = f'{dt.format("YYYY/MM/DD HH:mm")} - {dt.shift(minutes=meeting["duration"]).format("HH:mm")}'
    sorted_meetings[dt.datetime.date()].append((time, meeting["topic"]))

dt = arrow.get("2026/06/01")
dt = dt.replace(hour=19, minute=0)
existing_meetings = {}
# get existing GMT meetings, on 3rd Wed of each month
while True:
    if dt.month >= 6 and dt.year >= 2027:
        break
    dt = dt.shift(months=1)
    dt = dt.replace(day=1)
    while dt.weekday() != 2:
        dt = dt.shift(days=1)
    dt = dt.shift(weeks=2)
    sorted_meetings[dt.datetime.date()].append(
        (
            f'{dt.format("YYYY/MM/DD HH:mm")} - {dt.shift(minutes=90).format("HH:mm")}',
            "GMT/GET Meeting",
        )
    )

dt = arrow.get("2026/06/01")
dt = dt.replace(hour=19, minute=0)
# get existing meetings, on 2nd Thurs of each month
while True:
    if dt.month >= 6 and dt.year >= 2027:
        break
    dt = dt.shift(months=1)
    dt = dt.replace(day=1)
    while dt.weekday() != 3:
        dt = dt.shift(days=1)
    dt = dt.shift(weeks=1)
    sorted_meetings[dt.datetime.date()].append(
        (
            f'{dt.format("YYYY/MM/DD HH:mm")} - {dt.shift(minutes=90).format("HH:mm")}',
            "Generic Meeting",
        )
    )

dt = arrow.get("2026/09/01")
dt = dt.replace(hour=19, minute=0)
# get existing meetings, on 1st Thurs of every 3rd month
while True:
    if dt.month >= 6 and dt.year >= 2027:
        break
    dt = dt.shift(months=3)
    dt = dt.replace(day=1)
    while dt.weekday() != 3:
        dt = dt.shift(days=1)
    sorted_meetings[dt.datetime.date()].append(
        (
            f'{dt.format("YYYY/MM/DD HH:mm")} - {dt.shift(minutes=90).format("HH:mm")}',
            "MD410 Club Membership Chair Forum",
        )
    )

keys = list(sorted_meetings.keys())
keys.sort()
meetings = {}
for k in keys:
    meetings[k] = sorted_meetings[k]

print(meetings)
month = None
out = []
for k in meetings:
    if not month or k.month != month:
        if month:
            out.append("</ul>")
        month = k.month
        out.append("")
        out.append(f"<h3>{k:%B %Y}</h3><ul>")
    for meeting in meetings[k]:
        out.append(f"<li>{meeting[0]}</li>")
out.append("</ul>")
with open("zoom.html", "w") as fh:
    fh.write("\n".join(out))
