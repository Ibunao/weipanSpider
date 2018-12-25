# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.request import Request
from weipanSpider.items import WeipanspiderItem
import json
import re
import time

class WeipandirSpider(scrapy.Spider):
    '''
    根据目录资源来获取目录下的所有可下载的资源
    需要修改的参数
    target_url 要抓取的目标，如果是多页的建议赋值第二页的然后去掉页码
    route 保存的基础路径
    self.page['/'] 从第几页开始抓取
    dirpage 一个文件夹内如果还有文件夹B，那么这个文件夹B将会出现在所有分页的顶部，默认为1，只抓第一页上的文件夹
    '''
    name = 'weipandir'
    allowed_domains = ['weibo.com']

    # 抓取的目标url
    target_url = 'http://vdisk.weibo.com/s/z9WlaCbN77J2f?parents_ref=z9WlaCbN77J2f&category_id=0&pn='

    # 保存的基础路径。为了避免覆盖，建议爬取不同的用户时设置不同的目录
    route = 'temp'
    get_down_info = 'http://vdisk.weibo.com/api/weipan/fileopsStatCount?link={link}&ops=download&wpSign={sign}&_={time}'
    page = {}
    dirpage = 1
    def start_requests(self):
        self.page['/'] = 1
        # cookiejar 参数用来自动管理cookie  filepath为了记录目录，会传递给response
        return [Request(self.target_url+str(self.page), meta = {'cookiejar':1, 'filepath':'/'})]
    def parse(self, response):

        # 获取响应体
        # print(response.body)
        # 获取 SIGN
        sign = re.search("var SIGN = \'(.+)\';", response.text).group(1)
        # print(sign)
        items = response.xpath('//tbody/tr')
        # print(items)
        # 如果当前页没有，则进行下一页
        if not len(items):
            # 看是否有下一页
            nextpage = response.xpath('//div[@class="vd_page"]/a[@class="vd_bt_v2 vd_page_btn"]/span["下一页"]/text()')
            print('next page', nextpage, len(nextpage))
            if len(nextpage):
                yield self.my_process_next(response)


        for item in items:
            info = item.xpath('.//th/span/a[1]/@data-info').extract_first()
            print(info)
            info = json.loads(info)
            # 如果是文件夹
            if info['is_dir']:
                # 默认只抓子第一页的目录
                if self.page['/'] <= self.dirpage:
                    yield self.process_dir(info, response)
                continue

            href = self.get_down_info.format(link=info['copy_ref'], sign=sign, time = int(round(time.time() * 1000)))
            # print(href)
            yield Request(href, meta={'cookiejar': response.meta['cookiejar'], 'filepath': response.meta['filepath']}, callback=self.next)

        # 看是否有下一页
        nextpage = response.xpath('//div[@class="vd_page"]/a[@class="vd_bt_v2 vd_page_btn"]/span["下一页"]/text()')
        print('next page', nextpage, len(nextpage))
        if len(nextpage):
            yield self.my_process_next(response)

    # 注意：最后要用return，不能直接作用yield
    def my_process_next(self, response):
        '''
        获取下一页
        :param response:
        :return:
        '''
        if self.page.get(response.meta['filepath']) is None:
            self.page[response.meta['filepath']] = 1
        self.page[response.meta['filepath']] += 1
        # 测试前两页
        if self.page['/'] >= 3:
            return
        print('now page'+ response.meta['filepath'], self.page[response.meta['filepath']])
        return Request(self.target_url+str(self.page[response.meta['filepath']]), meta={'cookiejar': response.meta['cookiejar'], 'filepath': response.meta['filepath']}, callback=self.parse)

    # 注意：最后要用return，不能直接作用yield
    def process_dir(self, info, response):
        '''
        如果是目录
        :param info:
        :param response:
        :return:
        '''
        filepath = response.meta['filepath']+info['filename']+'/'
        return Request(info['link'], meta={'cookiejar': response.meta['cookiejar'], 'filepath': filepath}, callback=self.parse)

    def next(self, response):
        # print(response.body)
        info = json.loads(response.text)
        print({'fileurl': info['url'], 'filename': info['title'], 'path': self.route+response.meta['filepath']})
        witem = WeipanspiderItem(path = self.route+response.meta['filepath'], fileurl = info['url'], filename = info['title'])
        yield witem


