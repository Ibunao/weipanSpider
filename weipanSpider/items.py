# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy

class WeipanspiderItem(scrapy.Item):
    # define the fields for your item here like:
    fileurl = scrapy.Field()
    path = scrapy.Field()
    filename = scrapy.Field()
