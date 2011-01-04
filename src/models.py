"""
Models for persistent objects.
"""

from sqlalchemy import Column, String, Integer
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# SQLAlchemy initialisation

Base = declarative_base()
engine = create_engine('sqlite:///data/nuxeoorg.db', echo=True)
Session = sessionmaker(bind=engine)


# Abstract base class

class Source(object):
    type = ""

    def __init__(self):
        self.session = Session()

    def crawl(self):
        pass


class Event(Base):
    __tablename__ = "event"

    uid = Column(String, primary_key=True)
    type = Column(String)
    url = Column(String)
    author = Column(String)
    header = Column(String)
    title = Column(String)
    content = Column(String)
    created = Column(Integer)

Base.metadata.create_all(engine)