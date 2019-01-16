# -*- coding: utf-8 -*-
import os
import re
import sys
import json
import subprocess
import requests
from datetime import datetime
from dateutil import parser

# Add xcall folder to path so we can import it since
# we're using it as a submodule.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "xcall"))
import xcall


BEAR_API_TOKEN = os.getenv("BEAR_API_TOKEN")
if BEAR_API_TOKEN is None:
    raise Exception("Missing API Token")

PLANNER_TAG = "day planner"
TITLE_DAY_FORMAT = "%A %B %-d, %Y"
NOTE_BODY = u"""
## Todo:
{todo_items}

## Notes:


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

    todos = get_unfinished_todo_items()
    if not todos:
        todos = ["- [] Start doing something"]

    body = NOTE_BODY.format(agenda=agenda, weather=weather, todo_items="\n".join(todos))

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
    contents = xcall.xcall('bear', 'search', {"tag": PLANNER_TAG, "token": BEAR_API_TOKEN, "show_window": False, "term": search_term})
    notes = json.loads(contents['notes'])
    if len(notes) > 0:
        return contents['notes'][0]
    return None


def get_last_note():
    contents = xcall.xcall('bear', 'search', {"tag": PLANNER_TAG, "token": BEAR_API_TOKEN, "show_window": "no"})
    notes = json.loads(contents['notes'])
    last_note = None
    last_note_creation_date = None
    for note in notes:
        creation_date = parser.parse(note['creationDate'])
        if not last_note:
            last_note = note
            last_note_creation_date = creation_date
        else:
            if creation_date > last_note_creation_date:
                last_note = note
                last_note_creation_date = creation_date
    note = xcall.xcall('bear', 'open-note', {"id": last_note['identifier'], "new_window": "no", "show_window": "no"})
    return note


def get_unfinished_todo_items():
    last_note = get_last_note()
    note_body = last_note['note']
    lines = note_body.split('\n')
    pattern = re.compile('(?:- \[ \] )(.*)')

    existing_todos = []
    for line in lines:
        match = pattern.match(line)
        if match:
            existing_todos.append(match.group(0))

    return existing_todos


def create_daily_note():
    parameters = format_note()
    contents = xcall.xcall('bear', 'create', parameters)
    return contents


def main():
    # TODO: Get unchecked todo items from previous day and add them to current todo.
    # TODO: Remove morning time and evening time from calendar.
    if not get_existing_notes():
        create_daily_note()
        print("Daily note created!")
    else:
        print("Daily note already exists.")

if __name__ == "__main__":
    main()