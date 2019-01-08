# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import requests
from datetime import datetime

# Add xcall folder to path so we can import it since
# we're using it as a submodule.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "xcall"))
import xcall


BEAR_API_TOKEN = os.getenv("BEAR_API_TOKEN")
PLANNER_TAG = "day planner"
TITLE_DAY_FORMAT = "'%A %B %-d, %Y'"
NOTE_BODY = u"""
## Todo:
- [ ] Do something

## Today's Agenda:
{agenda}
## Weather Forecast:
{weather}
"""

def get_daily_agenda():
    command = ['icalbuddy -iep datetime,title,location -b "- " -ic patrick@noom.com -nc eventsToday']
    return subprocess.check_output(command, shell=True)


def get_weather():
    r = requests.get("http://wttr.in/?0&T")
    return u"```\n{}```".format(r.text)


def format_note():
    title = datetime.now().strftime(TITLE_DAY_FORMAT)
    tags = ",".join([PLANNER_TAG])
    agenda = get_daily_agenda()
    weather = get_weather()

    body = NOTE_BODY.format(agenda=agenda, weather=weather)

    return {
        "title": title,
        "tags": tags,
        "text": body,
        "open_note": True,
        "pin": True,
        "timestamp": True
    }


def get_existing_notes():
    search_term = datetime.now().strftime(TITLE_DAY_FORMAT)
    contents = xcall.xcall('bear', 'search', {"tag": PLANNER_TAG, "token": BEAR_API_TOKEN, "term": search_term})
    if len(contents['notes']) > 0:
        return contents['notes'][0]
    return None


def create_daily_note():
    parameters = format_note()
    contents = xcall.xcall('bear', 'create', parameters)
    return contents


def main():
    if not get_existing_notes():
        create_daily_note()
        print("Daily note created!")
    else:
        print("Daily note already exists.")

if __name__ == "__main__":
    main()