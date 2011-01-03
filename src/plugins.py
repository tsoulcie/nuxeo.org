import time, re
import feedparser

from models import Event, Source

#
# RSS / Atom Feed abstract class
#

class Feed(Source):
    """Abstract base class: do not instantiate."""

    feed_url = None

    def crawl(self):
        d = feedparser.parse(self.feed_url)
        self.source_url = d.href
        self.home_url = d.feed.link
        self.title = d.feed.title
        entries = d.entries

        events = [ self.make_event(entry) for entry in entries ]

        for event in events:
            self.session.add(event)
        self.session.commit()

    def make_event(self, entry):
        event = Event()
        event.type = self.type
        event.title = entry.title
        event.uid = entry.id
        event.url = entry.link
        event.created = time.mktime(entry.updated_parsed)
        event.author = entry.get("author", "unknown")
        self.post_init(event, entry)
        return event

    def post_init(self, event, entry):
        pass

#
# Instantiable sources
#

BLOG_AUTHORS = {
    "Stefane Fermigier": "Stefane Fermigier",
    "CherylMcKinnon": "Cheryl McKinnon",
    "Nuxeo": "Nuxeo Team",
    "eric's blog": "Eric Barroca",
    "My job things": "Roland Benedetti",
    "Sun Seng David TAN": "Sun Tan",
}

class Blogs(Feed):
    type = "blogpost"
    feed_url = "http://blogs.nuxeo.com/atom.xml"

    def post_init(self, event, entry):
        event.header = "New blog post by %s" % event.author

#

class CorpNews(Feed):
    type = "news"
    feed_url = "http://www.nuxeo.com/nxc/rssfeed/news"

    def post_init(self, event, entry):
        event.author = "Nuxeo Corp"
        event.header = "New Corporate announcement, on <a href='http://www.nuxeo.com/'>nuxeo.com</a>"

#

class Buzz(Feed):
    type = "buzz"
    feed_url = "http://www.nuxeo.com/en/rss/feed/buzz"

    def post_init(self, event, entry):
        event.author = "Nuxeo Corp"
        event.header = "Buzz about us, displayed on <a href='http://www.nuxeo.com/'>nuxeo.com</a>"

#

class Forum(Feed):
    type = "forum"
    feed_url = "http://forum.nuxeo.org/feed.php?mode=m&l=1&basic=1"

    def post_init(self, event, entry):
        m = re.match(r"http://forum.nuxeo.org/\./mv/msg/([0-9]+)/([0-9]+)", event.url)
        tid = int(m.group(1))
        mid = int(m.group(2))
        event.url = "http://forum.nuxeo.org/?t=msg&th=%d&goto=%d&#msg_%d" % (tid, mid, mid)
        event.header = "New message on the forum, by %s" % (event.author,)

#

class Documentation(Feed):
    type = "documentation"
    feed_url = "https://doc.nuxeo.com/spaces/createrssfeed.action?spaces=conf_all" + \
        "&types=page&types=comment&types=blogpost&types=mail&types=attachment" + \
        "&maxResults=15&publicFeed=true"

    def post_init(self, event, entry):
        event.header = "Documentation change, by %s" % event.author

#

class Jira(Feed):
    type = "jira"
    feed_url = "http://jira.nuxeo.org/sr/jira.issueviews:searchrequest-rss/10915/SearchRequest-10915.xml?tempMax=10"

    def post_init(self, event, entry):
        event.content = entry.description
        entry.description.encode("latin1", "ignore")
        if re.search("&nbsp;Updated: [0-9]{2}/[0-9]{2}/[0-9]{2}", event.content):
            self.header = "Jira issue change, by %s" % event.author
        else:
            self.header = "New Jira issue, by %s" % event.author

#############################################################################

all_sources = [Blogs(), Forum(), CorpNews(), Buzz(), Jira(), Documentation()]
