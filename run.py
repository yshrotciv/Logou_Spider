# -*- coding: utf-8 -*-

from twisted.internet import reactor

from crawler_manager import CrawlerManager

crawler_manager = CrawlerManager(reactor)
reactor.run()
