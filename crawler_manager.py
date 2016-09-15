# -*- coding: utf-8 -*-


from threading import Thread
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.conf import get_project_settings
from lagou.spiders.lagou_spider import LagouSpider, spider_opened, store_lagou_info
import config


class CrawlerManager(Thread):
    """
        the class manage the crawler
    """

    def __init__(self, reactor=None):
        super(CrawlerManager, self).__init__(name='crawler_manager')
        self.setDaemon(True)

        self.running_reactor = reactor

        self.lagou_spider = None
        self.signal_selector = {
            spider_opened: self.__lagou_spider_opened,
            store_lagou_info: self.__store_lagou_info
        }

        settings = get_project_settings()
        configure_logging(settings)
        self.crawler_process = CrawlerProcess(settings)
        self.crawler_process.crawl(LagouSpider, {'callback': self.spider_signal_parse})

        d = self.crawler_process.join()
        d.addCallback(lambda _: self.process_stop())

        self.task_list = []
        self.task_list.append(config.task)

        self.start()

    def run(self):
        while 1:
            if len(self.task_list) > 0:
                task = self.task_list.pop(0)
                self.lagou_spider.add_task(task)

    def spider_signal_parse(self, signal, params):
        if signal not in self.signal_selector.keys():
            return
        method = self.signal_selector[signal]
        if method:
            method(params)

    def __lagou_spider_opened(self, params):
        self.lagou_spider = params[0]

    @staticmethod
    def __store_lagou_info(item):
        with open('company_info.txt', 'a+') as fd:
            fd.write(item['company_name'])
            fd.write('\n')
            fd.write(item['salary'])
            fd.write('\n')
            fd.write(item['exp_request'])
            fd.write('\n')
            fd.write(item['description'])
            fd.write('\n\n')

    def process_stop(self):
        self.running_reactor.stop()
