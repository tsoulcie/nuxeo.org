#!/usr/bin/env python

import plugins

class Crawler(object):

    def __init__(self):
        self.all_sources = plugins.all_sources

    def crawl(self):
        for source in self.all_sources:
            #print "Crawling", source
            source.crawl()


if __name__ == '__main__':
    crawler = Crawler()
    crawler.crawl()
