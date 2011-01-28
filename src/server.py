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

def get_events(user=None, max_events=MAX_EVENTS):
    query = g.session.query(Event)
    if user:
        query = query.filter(Event.author == user)
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
        return "%d seconds ago" % dt
    if dt < 2*MINUTE:
        return "about 1 minute ago"
    if dt < HOUR:
        return "%d minutes ago" % (dt/MINUTE)
    if dt < 2*HOUR:
        return "about 1 hour ago"
    if dt < DAY:
        return "about %d hours ago" % (dt/HOUR)
    if dt < 2*DAY:
        return "yesterday"
    if dt < MONTH:
        return "about %d days ago" % (dt/DAY)
    if dt < 2*MONTH:
        return "last month"
    if dt < YEAR:
        return "about %d months ago" % (dt/MONTH)
    return "%d years ago" % (dt/YEAR)


if __name__ == '__main__':
    app.run(debug=True)

