#!env/bin/python

import time
from datetime import datetime

from flask import *
from werkzeug.contrib.atom import AtomFeed

from models import Event, Session


# Constants (might go into a config file)
MAX_EVENTS = 20

# Real constants
MINUTE = 60
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


@app.route('/')
def home():
    try:
        visits = int(request.cookies.get('visits', 0)) + 1
    except ValueError:
        visits = 0
    is_newbie = visits < 3

    events = get_events()
    response = make_response(render_template("home.html", events=events, is_newbie=is_newbie))

    response.set_cookie('visits', visits, 10*YEAR)
    return response

def get_events():
    events = g.session.query(Event).order_by(Event.created.desc()).limit(MAX_EVENTS)
    return events


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

