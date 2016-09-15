# -*- coding: utf-8 -*-

from scrapy.spiders import Spider
from scrapy.http import FormRequest, Request
from scrapy.signals import spider_opened
from scrapy.xlib.pydispatch import dispatcher
from scrapy.selector import Selector
from urllib import quote
import json

store_lagou_info = object()


class LagouSpider(Spider):
    """
        the logic implementation of crawling lagou
    """

    name = 'lagou'

    def __init__(self, params):
        super(LagouSpider, self).__init__()
        self.signal_callback = params['callback']

        self.company_base_url = 'http://www.lagou.com/jobs/%s.html'
        self.task_url = 'http://www.lagou.com/jobs/positionAjax.json?'
        self.referer = 'http://www.lagou.com/zhaopin/'
        self.headers = {
            'Referer': self.referer,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/52.0.2743.116 Safari/537.36'
        }
        self.quote_kd = None

        self.total_pages = 0
        self.page_flag = 1
        self.post_data = {
            'city': '',
            'needAddtionalResult': 'false',
            'first': 'true',
            'pn': '1',
            'kd': ''
        }
        dispatcher.connect(self.spider_signal_triggered)

    def add_task(self, task):
        self.post_data['kd'] = task['kd']
        self.post_data['city'] = task['city']
        self.quote_kd = quote(self.post_data['kd'])
        first_req = FormRequest(
            url=self.task_url,
            callback=self.parse,
            formdata=self.post_data,
            headers=self.headers
        )
        self.crawler.engine.schedule(first_req, self)

    def parse(self, response):
        resp_dict = json.loads(response.body)
        for result in resp_dict['content']['positionResult']['result']:
            position_id = result['positionId']
            company_url = self.company_base_url % position_id
            self.headers[
                'Referer'] = 'http://www.lagou.com/jobs/list_%s?labelWords=&fromSearch=true&suginput=' % self.quote_kd
            company_req = Request(
                url=company_url,
                callback=self.parse_company,
                headers=self.headers
            )
            self.crawler.engine.schedule(company_req, self)

        if self.page_flag == 1:
            self.total_pages = int(resp_dict['content']['positionResult']['totalCount'] / 15 + 1)
            for pn in range(2, self.total_pages + 1):
                self.post_data['pn'] = str(pn)
                self.post_data['first'] = 'false'
                next_req = FormRequest(
                    url=self.task_url,
                    callback=self.parse,
                    formdata=self.post_data,
                    headers=self.headers
                )
                self.crawler.engine.schedule(next_req, self)
            self.page_flag -= 1

    def parse_company(self, response):
        sel = Selector(response)
        item = {}

        company_name = sel.xpath('//img[@class="b2"]/@alt')[0].extract().encode('utf-8')
        item['company_name'] = company_name

        job_request_label = sel.xpath('//dd[@class="job_request"]')[0]
        item['salary'] = job_request_label.xpath('p[1]/span[1]/text()')[0].extract().encode('utf-8')
        item['exp_request'] = job_request_label.xpath('p[1]/span[3]/text()')[0].extract().encode('utf-8')

        job_description_label = sel.xpath('//dd[@class="job_bt"]')[0]
        item['description'] = job_description_label.xpath('string(.)')[0].extract().encode('utf-8')
        # print item['salary'], item['exp_request'], item['description'], item['company_name']
        self.signal_callback(store_lagou_info, item)

    def spider_signal_triggered(self, signal):
        if signal == spider_opened:
            self.signal_callback(spider_opened, [self, ])
