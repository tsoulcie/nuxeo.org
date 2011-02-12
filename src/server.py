#!env/bin/python
import math

import time
from datetime import datetime

from flask import *
import plugins
from werkzeug.contrib.atom import AtomFeed

from models import Event, Session


# Constants (might go into a config file)
MAX_EVENTS = 25

# Real constants
MINUTE = 60.0
HOUR = 60*MINUTE
DAY = 24*HOUR
MONTH = 30*DAY
YEAR = 365*DAY


# Use /media instead of default /static because /static is already used.
app = Flask(__name__, static_path='/media')


@app.before_request
def connect_db():
    g.session = Session()

@app.before_request
def register_helpers():
    g.age = age

# REST endpoints

@app.route('/')
def home():
    try:
        visits = int(request.cookies.get('visits', 0)) + 1
    except ValueError:
        visits = 0
    is_newbie = visits < 3

    events = get_events(max_events=10*MAX_EVENTS)
    events = filter_events(events)

    response = make_response(render_template("home.html", events=events, is_newbie=is_newbie))

    response.set_cookie('visits', visits, 10*YEAR)
    return response

@app.route('/user/<username>')
def user(username):
    events = get_events(user=username)
    response = make_response(render_template("user.html", username=username, events=events))
    return response

@app.route('/archive/<year>/<month>/<day>')
def user(year, month, day):
    date = datetime(int(year), int(month), int(day))
    events = get_events(date=date)
    response = make_response(render_template("archive.html", date=date, events=events))
    return response


@app.route('/rss')
def feed():
    feed = AtomFeed("Nuxeo Community Feed", feed_url=request.url,
                    url=request.host_url,
                    subtitle="What's happening now in the Nuxeo community.")
    for event in get_events():
        if event.type == 'documentation':
            continue
        # TODO: Escape strings
        content = "<p><em>%s:</em></p>" % event.header \
            + event.content \
            + "<p><em>URL: <a href='%s'>%s</a></em></p>" % (event.url, event.url)
        title = event.type.capitalize() + " - " + event.title
        feed.add(title=title, content=content, content_type='text/html',
                 author=event.author, url=event.url, id=event.uid,
                 updated=datetime.utcfromtimestamp(event.created),
                 published=datetime.utcfromtimestamp(event.created))
    return feed.get_response()

# Debug
@app.route('/rss-debug')
def feed_debug():
    return feed()

# Utility functions

def get_events(user=None, date=None, max_events=MAX_EVENTS):
    query = g.session.query(Event)
    if user:
        query = query.filter(Event.author == user)
    if date:
        ts = time.mktime(date.timetuple())
        query = query.filter(Event.created >= ts).filter(Event.created < ts+DAY)
    events = query.order_by(Event.created.desc()).limit(max_events)
    print events
    return events[:]

def filter_events(events):
    already_seen = {}
    now = int(time.time())
    for e in events:
        half_life = plugins.get_half_life_for(e)
        decay = math.exp(-(now - e.created) / (DAY * half_life))
        #key = e.title + "::" + e.author
        title = e.title.lower()
        while title.startswith("re: "):
            title = title[4:]
        key = title
        if already_seen.has_key(key):
            decay = 0
        already_seen[key] = None
        e.decay = decay
    events.sort(lambda x, y: -cmp(x.decay, y.decay))
    events = events[0:MAX_EVENTS]
    events.sort(lambda x, y: -cmp(x.created, y.created))
    return events


def age(t):
    now = int(time.time())
    dt = now - t
    if dt < MINUTE:
        age = "%d seconds ago" % dt
    elif dt < 2*MINUTE:
        age = "about 1 minute ago"
    elif dt < HOUR:
        age = "%d minutes ago" % (dt/MINUTE)
    elif dt < 2*HOUR:
        age = "about 1 hour ago"
    elif dt < DAY:
        age = "about %d hours ago" % (dt/HOUR)
    elif dt < 2*DAY:
        age = "yesterday"
    elif dt < MONTH:
        age = "about %d days ago" % (dt/DAY)
    elif dt < 2*MONTH:
        age = "last month"
    elif dt < YEAR:
        age = "about %d months ago" % (dt/MONTH)
    else:
        age = "%d years ago" % (dt/YEAR)
    date = datetime.utcfromtimestamp(t)
    return '<a href="/archive/%d/%d/%d">%s</a>' % (date.year, date.month, date.day, age)


if __name__ == '__main__':
    app.run(debug=True)

