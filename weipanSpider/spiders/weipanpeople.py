# -*- coding: utf-8 -*-
import scrapy
from scrapy.http.request import Request
from weipanSpider.items import WeipanspiderItem
import json
import re
import time

class WeipanpeopleSpider(scrapy.Spider):
    '''
    下载某用户分享的所有电子书
    需要修改的参数
    target_url 要抓取的目标，如果是多页的建议赋值第二页的然后去掉页码
    route 保存的基础路径
    self.page['/'] 从第几页开始抓取
    dirpage 一个文件夹内如果还有文件夹B，那么这个文件夹B将会出现在所有分页的顶部，默认为1，只抓第一页上的文件夹
    '''
    name = 'weipanpeople'
    allowed_domains = ['weibo.com']
    # 首页数据
    target_url = 'http://vdisk.weibo.com/u/1881788364?page='
    # 基础路径，爬取不同的用户需要设置一下
    route = 'people'
    get_down_info = 'http://vdisk.weibo.com/api/weipan/fileopsStatCount?link={link}&ops=download&wpSign={sign}&_={time}'
    page = {'/': 1}
    dirpage = 1
    dirtarget_url = {}

    def start_requests(self):
        # cookiejar 参数用来自动管理cookie  filepath为了记录目录，会传递给response
        return [Request(self.target_url + str(self.page['/']), meta={'cookiejar': 1, 'filepath': '/'})]

    def parse(self, response):

        # 获取响应体
        # print(response.body)
        # 获取 SIGN
        sign = re.search("var SIGN = \'(.+)\';", response.text).group(1)
        # print(sign)
        items = response.xpath('//tbody/tr')
        # print(items)
        # 如果当前页没有，则进行下一页(很多情况是第一页没有，而从某个分页开始才有资源，可能是因为最近资源查封的原因)
        if not len(items):
            # 看是否有下一页
            nextpage = response.xpath('//div[@class="vd_page"]/a[@class="vd_bt_v2 vd_page_btn"]/span["下一页"]/text()')
            print('next page', nextpage, len(nextpage))
            if len(nextpage):
                yield self.my_process_next(response)

        for item in items:
            # 从用户首页进入 xpath 是和其他入口有一些区别的
            if response.meta['filepath'] == '/':
                # 用户首页时的xpath
                xpath = './/td[2]/span/a[1]/@data-info'
            else:
                # 其他入口的 xpath
                xpath = './/th/span/a[1]/@data-info'
            info = item.xpath(xpath).extract_first()
            print(info)
            info = json.loads(info)
            # 如果是文件夹
            if info['is_dir']:
                # 默认只抓子第一页的目录
                if self.page['/'] <= self.dirpage:
                    yield self.process_dir(info, response)
                continue

            href = self.get_down_info.format(link=info['copy_ref'], sign=sign, time=int(round(time.time() * 1000)))
            # print(href)
            yield Request(href, meta={'cookiejar': response.meta['cookiejar'], 'filepath': response.meta['filepath']},
                          callback=self.next)

        # 看是否有下一页 这个获取下一页还是有点问题，偶尔会一直往下循环
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
        # 记录不同目录的分页
        if self.page.get(response.meta['filepath']) is None:
            self.page[response.meta['filepath']] = 1
        self.page[response.meta['filepath']] += 1
        # 测试下载 只下载第一页
        # if response.meta['filepath'] == '/' and self.page['/'] >= 2:
        #     return

        # 防止一直往下循环的bug 目前限定50页
        if self.page[response.meta['filepath']] >= 50:
            return

        if self.dirtarget_url.get(response.meta['filepath']) is None:
            target_url = self.target_url
        else:
            target_url = self.dirtarget_url.get(response.meta['filepath'])
        print('now page' + response.meta['filepath'], self.page[response.meta['filepath']])
        return Request(target_url + str(self.page[response.meta['filepath']]),
                       meta={'cookiejar': response.meta['cookiejar'], 'filepath': response.meta['filepath']},
                       callback=self.parse)

    # 注意：最后要用return，不能直接作用yield
    def process_dir(self, info, response):
        '''
        如果是目录
        :param info:
        :param response:
        :return:
        '''

        filepath = response.meta['filepath'] + info['filename'] + '/'
        # 保存不同目录的链接
        self.dirtarget_url[filepath] = info['url'] + '&pn='
        return Request(info['url'], meta={'cookiejar': response.meta['cookiejar'], 'filepath': filepath},
                       callback=self.parse)

    def next(self, response):
        # print(response.body)
        info = json.loads(response.text)
        print({'fileurl': info['url'], 'filename': info['title'], 'path': self.route + response.meta['filepath']})
        witem = WeipanspiderItem(path=self.route + response.meta['filepath'], fileurl=info['url'],
                                 filename=info['title'])
        yield witem

