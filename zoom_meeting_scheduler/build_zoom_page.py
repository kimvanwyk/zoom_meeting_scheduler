import arrow
import csv
from rich import print

meetings = []
with open("zoom_meetings.csv", "r") as fh:
    rdr = csv.DictReader(fh, delimiter="|")
    for r in rdr:
        meetings.append((r["timestamp"], r["date_description"]))
meetings.sort()
print(meetings)

month = None
out = []
for meeting in meetings:
    dt = arrow.get(meeting[0])
    if not month or dt.month != month:
        if month:
            out.append("</ul>")
        month = dt.month
        out.append("")
        out.append(f"          <h3>{dt.format('MMMM YYYY')}</h3>")
        out.append(f"          <ul>")
    out.append(f"            <li>{meeting[1]}</li>")
out.append("          </ul>")
with open("zoom.html", "w") as fh:
    with open("page_preamble.html", "r") as fin:
        fh.write(fin.read())
    fh.write("\n".join(out))
    with open("page_postamble.html", "r") as fin:
        fh.write(fin.read())
