# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

from scrapy import signals


class WeipanspiderSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class WeipanspiderDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


import random
import requests
import json
import redis
from scrapy.utils.project import get_project_settings

class RandomIpproxy:
    '''
    代理不行，之后的代码还没有实现，如果一个代理异常，删除这个代理，重新请求，当代理数小于3时重新获取代理添加到redis
    '''
    redis = None
    '''
    代理中间件
    '''
    def __init__(self, iplist):
        # print(type(iplist), iplist)
        self.iplist = iplist

    @classmethod
    def from_crawler(cls, crawler):
        return cls(cls.get_ipproxy())

    def process_request(self, request, spider):
        proxy = random.choice(self.iplist)
        if proxy:
            print(proxy, type(proxy))
            request.meta['proxy'] = 'http://121.235.202.194:65309'


    @classmethod
    def get_ipproxy(cls):
        if cls.get_redis():
            len = cls.redis.llen('ipproxy')
            if len:
                return cls.redis.lrange('ipproxy', 0, len)
            else:
                type = 'http'
                res = requests.get('http://lab.crossincode.com/proxy/get/?num=5&head={}'.format(type))
                temp = json.loads(res.text)
                iplist = []
                if temp['code'] == 1:
                    list = temp['proxies']
                    for item in list:
                        # print(item)
                        iplist.append('http://'+item[type])
                cls.redis.lpush('ipproxy', *tuple(iplist))
                return iplist

    def process_exception(self, request, exception, spider):
        '''
        处理异常
        :param request:
        :param exception:
        :param spider:
        :return:
        '''
        # 捕捉异常
        print(exception)

    @classmethod
    def get_redis(cls):
        if cls.redis:
            return cls.redis
        settings = get_project_settings();

        red = redis.Redis(host=settings['REDIS_HOST'], port=settings['REDIS_PORT'], db=settings['REDIS_DB'], decode_responses=True)
        if red:
            # print(red)
            cls.redis = red
            return red
        raise Exception('get_redis error')
